# eval/run_eval.py
"""
Project Aegis — Evaluation Runner
===================================
Runs the golden QA dataset through the full Aegis pipeline and measures:

  1. Retrieval Recall@5
     Did the correct source document appear in the top-5 retrieved chunks?

  2. Answer Faithfulness (LLM-as-judge)
     Does the answer contain all required keywords from the expected answer?
     Scored 0.0 – 1.0 (fraction of keywords present).

  3. Category Detection Accuracy
     Did detect_category() return the correct policy category?

Usage:
    python -m eval.run_eval

Output:
    - Console summary table
    - eval/results/eval_results_<timestamp>.json
    - eval/results/eval_summary_<timestamp>.txt
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr
from openai import OpenAI
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI

from chat import ask
from retrieval.filters import detect_category
from eval.golden_qa import GOLDEN_QA

load_dotenv()
logging.basicConfig(level=logging.WARNING)

# ── Setup ──────────────────────────────────────────────────────────────────────
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
qdrant_client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60
)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=SecretStr(os.environ["OPENAI_API_KEY"])
)

# Output folder
RESULTS_DIR = Path("eval/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Metric helpers ─────────────────────────────────────────────────────────────

def recall_at_5(sources: list[dict], expected_doc_id: str) -> float:
    """
    Returns 1.0 if the expected source document appears in the top-5
    retrieved chunks, else 0.0.
    Handles both 'document_id' and nested metadata['document_id'].
    """
    retrieved_doc_ids = []
    for s in sources:
        # Try top-level key first (chat.py builds it this way)
        doc_id = s.get("document_id") or s.get("doc_id")
        # Fall back to metadata dict if present
        if not doc_id and isinstance(s.get("metadata"), dict):
            doc_id = s["metadata"].get("document_id")
        if doc_id:
            retrieved_doc_ids.append(doc_id)
    return 1.0 if expected_doc_id in retrieved_doc_ids else 0.0


def keyword_faithfulness(answer: str, keywords: list[str]) -> float:
    """
    Fraction of required keywords present in the answer (case-insensitive).
    Score of 1.0 means all keywords found — fully faithful to expected answer.
    """
    answer_lower = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return round(hits / len(keywords), 3) if keywords else 0.0


def category_accuracy(question: str, expected_category: str) -> tuple[str, bool]:
    """
    Runs detect_category on the question and checks if it matches expected.
    Returns (detected_category, is_correct).
    """
    detected = detect_category(question, llm) or "None"
    return detected, (detected == expected_category)


# ── Main eval loop ─────────────────────────────────────────────────────────────

def run_eval():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    print("\n" + "=" * 70)
    print(f"  Project Aegis — Evaluation Run  [{timestamp}]")
    print(f"  Dataset: {len(GOLDEN_QA)} questions")
    print("=" * 70)

    for i, qa in enumerate(GOLDEN_QA, start=1):
        qid = qa["id"]
        question = qa["question"]
        expected_doc = qa["source_doc"]
        expected_category = qa["category"]
        keywords = qa["keywords"]

        print(f"\n[{i:02d}/{len(GOLDEN_QA)}] {qid} — {question[:60]}...")

        # ── Run full pipeline ──────────────────────────────────────────────
        try:
            result = ask(
                query=question,
                session_id=f"eval_{qid}",
                qdrant=qdrant_client,
                openai_client=openai_client,
                llm=llm
            )
            answer = result["answer"]
            sources = result["sources"]
            token_info = result.get("token_info", {})

        except Exception as e:
            print(f"  ❌ Pipeline error: {e}")
            results.append({
                "id": qid,
                "question": question,
                "error": str(e),
                "recall_at_5": 0.0,
                "faithfulness": 0.0,
                "category_correct": False,
            })
            continue

        # ── Score ──────────────────────────────────────────────────────────
        recall = recall_at_5(sources, expected_doc)
        faith = keyword_faithfulness(answer, keywords)
        detected_cat, cat_correct = category_accuracy(question, expected_category)

        # ── Print row ──────────────────────────────────────────────────────
        recall_icon = "✓" if recall == 1.0 else "✗"
        cat_icon = "✓" if cat_correct else "✗"
        print(f"  Recall@5:     {recall_icon}  ({recall:.1f})")
        print(f"  Faithfulness: {faith:.2f}  (keywords: {keywords})")
        print(f"  Category:     {cat_icon}  expected={expected_category}, got={detected_cat}")
        print(f"  Tokens used:  {token_info.get('total_tokens_after', 'N/A')}")

        results.append({
            "id": qid,
            "question": question,
            "expected_doc": expected_doc,
            "expected_category": expected_category,
            "detected_category": detected_cat,
            "answer_preview": answer[:300],
            "retrieved_docs": [
                s.get("document_id") or s.get("doc_id") or
                (s.get("metadata") or {}).get("document_id", "unknown")
                for s in sources
            ],
            "recall_at_5": recall,
            "faithfulness": faith,
            "category_correct": cat_correct,
            "tokens_used": token_info.get("total_tokens_after", None),
            "truncated": token_info.get("truncated", False),
        })

    # ── Aggregate metrics ──────────────────────────────────────────────────────
    n = len(results)
    avg_recall = round(sum(r["recall_at_5"] for r in results) / n, 3)
    avg_faith = round(sum(r["faithfulness"] for r in results) / n, 3)
    cat_acc = round(sum(1 for r in results if r.get("category_correct")) / n, 3)
    truncated_count = sum(1 for r in results if r.get("truncated"))

    summary = {
        "timestamp": timestamp,
        "total_questions": n,
        "avg_recall_at_5": avg_recall,
        "avg_faithfulness": avg_faith,
        "category_accuracy": cat_acc,
        "truncated_queries": truncated_count,
        "results": results,
    }

    # ── Save JSON ──────────────────────────────────────────────────────────────
    json_path = RESULTS_DIR / f"eval_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ── Save human-readable summary ────────────────────────────────────────────
    txt_path = RESULTS_DIR / f"eval_summary_{timestamp}.txt"
    summary_lines = [
        f"Project Aegis — Eval Summary [{timestamp}]",
        "=" * 50,
        f"Total questions     : {n}",
        f"Retrieval Recall@5  : {avg_recall:.1%}",
        f"Answer Faithfulness : {avg_faith:.1%}",
        f"Category Accuracy   : {cat_acc:.1%}",
        f"Token truncations   : {truncated_count}/{n}",
        "",
        "Per-question breakdown:",
        "-" * 50,
    ]
    for r in results:
        line = (
            f"{r['id']:<6} | Recall={r['recall_at_5']:.1f} | "
            f"Faith={r['faithfulness']:.2f} | "
            f"Cat={'PASS' if r.get('category_correct') else 'FAIL'} | "
            f"{r['question'][:45]}"
        )
        summary_lines.append(line)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    # ── Print final summary ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Retrieval Recall@5  : {avg_recall:.1%}  (did correct doc appear in top-5?)")
    print(f"  Answer Faithfulness : {avg_faith:.1%}  (keyword coverage of expected answer)")
    print(f"  Category Accuracy   : {cat_acc:.1%}  (detect_category correct?)")
    print(f"  Token truncations   : {truncated_count}/{n} queries hit budget limit")
    print(f"\n  Full results -> {json_path}")
    print(f"  Summary     -> {txt_path}")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_eval()
