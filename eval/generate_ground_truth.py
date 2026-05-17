# eval/generate_ground_truth.py
"""
Generates 25–30 ground truth Q&A pairs from Aegis policy documents using GPT.
Run this ONCE to create eval/ground_truth.json.

Usage:
    python -m eval.generate_ground_truth
"""

import os
import json
import glob
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

# ── CONFIG ──────────────────────────────────────────────────────────────────
DATA_DIR = "data"
OUTPUT_PATH = "eval/ground_truth.json"
QUESTIONS_PER_DOC = 3  # 3 per doc × 8 docs = 24 + a few extras = ~28
MODEL = "gpt-4o-mini"
# ─────────────────────────────────────────────────────────────────────────────

POLICY_CATEGORY_MAP = {
    "travel policy": "Travel",
    "international travel": "Travel",
    "fuel and mileage": "Travel",
    "learning and tuition": "HR",
    "leave_and_absence": "HR",
    "performance and compensation": "HR",
    "code of conduct": "HR",
    "it security": "IT",
}


def detect_category_from_filename(filepath: str) -> str:
    name = Path(filepath).stem.lower()
    for keyword, cat in POLICY_CATEGORY_MAP.items():
        if keyword in name:
            return cat
    return "Other"


def load_policy_docs(data_dir: str) -> list[dict]:
    """Load all .md files from the data directory tree."""
    docs = []
    for filepath in glob.glob(f"{data_dir}/**/*.md", recursive=True):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        category = detect_category_from_filename(filepath)
        docs.append(
            {
                "filepath": filepath,
                "filename": Path(filepath).name,
                "category": category,
                "content": content,
            }
        )
        logger.info("Loaded: %s  [%s]", filepath, category)
    return docs


def generate_qa_for_doc(
    doc: dict, client: OpenAI, n: int = QUESTIONS_PER_DOC
) -> list[dict]:
    """Ask GPT to generate n Q&A pairs from a single policy document."""

    # Truncate to ~6000 chars to stay within token limits
    content_snippet = doc["content"][:6000]

    prompt = f"""You are a corporate HR/Compliance expert creating an evaluation dataset.

Read the policy document below and generate exactly {n} question-answer pairs.

Rules:
1. Questions must be specific and answerable from the document text only.
2. Answers must be precise — include specific numbers, dates, percentages, limits where they exist.
3. Vary question types: some factual ("What is the limit?"), some procedural ("How do I...?"), some conditional ("What happens if...?").
4. Do NOT ask vague or generic questions.
5. Return ONLY a JSON array. No preamble, no markdown, no extra text.

Output format (strict JSON):
[
  {{
    "question": "...",
    "ground_truth": "...",
    "source_doc": "{doc['filename']}",
    "category": "{doc['category']}"
  }},
  ...
]

Policy Document:
---
{content_snippet}
---

Generate {n} Q&A pairs now:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = (
            "\n".join(lines[1:-1])
            if lines[-1].strip() == "```"
            else "\n".join(lines[1:])
        )

    try:
        pairs = json.loads(raw)
        logger.info("  Generated %d Q&A pairs for %s", len(pairs), doc["filename"])
        return pairs
    except json.JSONDecodeError as e:
        logger.error(
            "  JSON parse error for %s: %s\nRaw output:\n%s", doc["filename"], e, raw
        )
        return []


def main():
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    logger.info("=== Loading policy documents ===")
    docs = load_policy_docs(DATA_DIR)
    logger.info("Found %d documents", len(docs))

    all_qa_pairs = []

    logger.info("\n=== Generating Q&A pairs ===")
    for doc in docs:
        pairs = generate_qa_for_doc(doc, client)
        all_qa_pairs.extend(pairs)

    # Add a few cross-document / edge-case questions manually
    extra_pairs = [
        {
            "question": "If I resign 18 months after receiving tuition reimbursement, how much do I need to repay?",
            "ground_truth": "50% of the reimbursed funds must be repaid if departure occurs between 12 and 24 months of the payout date.",
            "source_doc": "learning and tuition.md",
            "category": "HR",
        },
        {
            "question": "What is the mileage reimbursement rate for personal vehicles and what does it cover?",
            "ground_truth": "$0.69 USD per business mile. The rate covers petrol/diesel, routine maintenance, oil changes, tire wear, depreciation, and personal auto insurance.",
            "source_doc": "fuel and mileage policy.md",
            "category": "Travel",
        },
        {
            "question": "Can employees traveling to China bring their standard corporate laptops?",
            "ground_truth": "No. Employees traveling to countries categorized as High Cyber-Risk such as China are strictly prohibited from bringing standard-issue corporate laptops. They must request Clean or Burner devices from IT Procurement 14 days prior to travel.",
            "source_doc": "international travel.md",
            "category": "Travel",
        },
    ]
    all_qa_pairs.extend(extra_pairs)

    logger.info("\n=== Summary ===")
    logger.info("Total Q&A pairs generated: %d", len(all_qa_pairs))

    # Category breakdown
    from collections import Counter

    cats = Counter(p["category"] for p in all_qa_pairs)
    for cat, count in sorted(cats.items()):
        logger.info("  %-15s  %d questions", cat, count)

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

    logger.info("\nSaved to: %s", OUTPUT_PATH)
    logger.info("Run next: python -m eval.run_ragas_eval")


if __name__ == "__main__":
    main()
