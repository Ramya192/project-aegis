# eval/run_ragas_eval.py
"""
Runs RAGAS evaluation on Project Aegis using the actual retrieval pipeline.
Measures all 6 RAG Triad metrics:
  Retrieval:   Context Precision, Context Recall, Context Relevancy
  Generation:  Faithfulness, Answer Relevancy, Answer Correctness

Prerequisites:
    pip install ragas datasets

Usage:
    python -m eval.run_ragas_eval
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROUND_TRUTH_PATH = "eval/ground_truth.json"
RESULTS_DIR = "eval/results"
MODEL = "gpt-4o-mini"
MAX_SAMPLES = 30  # set to None to run all
# ─────────────────────────────────────────────────────────────────────────────


def load_ground_truth(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        pairs = json.load(f)
    logger.info("Loaded %d Q&A pairs from %s", len(pairs), path)
    return pairs


def build_pipeline_clients():
    """Initialise Qdrant, OpenAI, and LangChain LLM — same as chat.py."""
    import os
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    qdrant_client = QdrantClient(
        url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=60
    )
    llm = ChatOpenAI(model=MODEL, api_key=SecretStr(os.environ["OPENAI_API_KEY"]))
    return qdrant_client, openai_client, llm


def run_pipeline_for_sample(question: str, qdrant, openai_client, llm) -> dict:
    """
    Run the actual Aegis pipeline for one question.
    Retries once on transient errors (Qdrant 502, OpenAI timeout).
    Returns: answer (str), retrieved_contexts (list of str)
    """
    from chat import ask
    import uuid
    import time

    for attempt in (1, 2):
        session_id = str(uuid.uuid4())
        try:
            result = ask(
                query=question,
                session_id=session_id,
                qdrant=qdrant,
                openai_client=openai_client,
                llm=llm,
            )
            return {
                "answer": result["answer"],
                "contexts": [s["text_preview"] for s in result["sources"]],
                "category_detected": result.get("category_detected"),
                "error": None,
            }
        except Exception as e:
            if attempt == 1:
                logger.warning(
                    "Attempt 1 failed for '%s...': %s — retrying in 5s",
                    question[:50],
                    e,
                )
                time.sleep(5)
            else:
                logger.error(
                    "Attempt 2 failed for '%s...': %s — skipping", question[:50], e
                )
                return {
                    "answer": "",
                    "contexts": [],
                    "category_detected": None,
                    "error": str(e),
                }


def build_ragas_dataset(samples: list[dict], qdrant, openai_client, llm) -> dict:
    """
    Run the Aegis pipeline for every sample and build the RAGAS input dataset.
    RAGAS expects:
        question     : str
        answer       : str   (LLM's actual answer)
        contexts     : list[str]  (retrieved chunks)
        ground_truth : str   (reference answer — required for Recall + Correctness)
    """
    questions, answers, contexts, ground_truths = [], [], [], []
    errors = []

    for i, sample in enumerate(samples):
        logger.info(
            "[%d/%d] Running pipeline: %s", i + 1, len(samples), sample["question"][:70]
        )

        result = run_pipeline_for_sample(
            question=sample["question"],
            qdrant=qdrant,
            openai_client=openai_client,
            llm=llm,
        )

        if result["error"]:
            errors.append({"question": sample["question"], "error": result["error"]})
            continue

        questions.append(sample["question"])
        answers.append(result["answer"])
        contexts.append(result["contexts"])
        ground_truths.append(sample["ground_truth"])

    logger.info(
        "Pipeline run complete. Successful: %d | Errors: %d",
        len(questions),
        len(errors),
    )
    if errors:
        logger.warning("Failed questions: %s", json.dumps(errors, indent=2))

    return {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }


def run_ragas_evaluation(dataset_dict: dict) -> dict:
    """Run RAGAS on the collected dataset and return metric scores.

    Compatible with RAGAS >= 0.2 which requires instantiated metric objects
    and uses LangchainLLMWrapper / LangchainEmbeddingsWrapper for LLM wiring.
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from pydantic import SecretStr

    # ── Import metric CLASSES (RAGAS >= 0.2 requires instantiated objects) ──
    try:
        from ragas.metrics import (
            ContextPrecision,
            ContextRecall,
            Faithfulness,
            AnswerRelevancy,
            AnswerCorrectness,
        )

        # ContextRelevancy renamed in some versions — try both
        try:
            from ragas.metrics import ContextRelevancy

            has_relevancy = True
        except ImportError:
            try:
                from ragas.metrics import NoiseSensitivity as ContextRelevancy

                has_relevancy = True
            except ImportError:
                has_relevancy = False
                logger.warning(
                    "ContextRelevancy not available in this RAGAS version — skipping"
                )
    except ImportError as e:
        logger.error("Could not import RAGAS metric classes: %s", e)
        raise

    logger.info("\n=== Running RAGAS Evaluation ===")
    logger.info("Samples: %d", len(dataset_dict["question"]))

    dataset = Dataset.from_dict(dataset_dict)

    # ── Wire LLM + Embeddings via RAGAS wrappers ──────────────────────────
    ragas_llm = LangchainLLMWrapper(
        ChatOpenAI(model=MODEL, api_key=SecretStr(os.environ["OPENAI_API_KEY"]))
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
        )
    )

    # ── Instantiate metrics (RAGAS >= 0.2 requirement) ────────────────────
    metrics = [
        ContextPrecision(),
        ContextRecall(),
        Faithfulness(),
        AnswerRelevancy(),
        AnswerCorrectness(),
    ]
    if has_relevancy:
        metrics.insert(2, ContextRelevancy())

    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        raise_exceptions=False,
    )

    return results


def format_and_save_results(ragas_results, dataset_dict: dict, samples: list[dict]):
    """Pretty-print results and save JSON + TXT to eval/results/."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Convert to dict
    scores = ragas_results.to_pandas().mean(numeric_only=True).to_dict()

    # ── Category breakdown ─────────────────────────────────────────────────
    category_scores = defaultdict(lambda: defaultdict(list))
    df = ragas_results.to_pandas()

    if "question" in df.columns:
        q_to_cat = {s["question"]: s["category"] for s in samples}
        df["category"] = df["question"].map(q_to_cat).fillna("Unknown")

        for metric in [
            "context_precision",
            "context_recall",
            "faithfulness",
            "answer_relevancy",
            "answer_correctness",
            "context_relevancy",
            "noise_sensitivity",
        ]:
            if metric in df.columns:
                for _, row in df.iterrows():
                    cat = row.get("category", "Unknown")
                    val = row.get(metric)
                    if val is not None and str(val) != "nan":
                        category_scores[cat][metric].append(float(val))

    # ── Console output ─────────────────────────────────────────────────────
    separator = "=" * 60
    print(f"\n{separator}")
    print("  PROJECT AEGIS — RAGAS EVALUATION RESULTS")
    print(f"  Run: {timestamp}")

    def fmt(val):
        """Format a metric score or return N/A if unavailable."""
        return f"{float(val):.3f}" if val != "N/A" and val is not None else " N/A "

    print(f"  Samples evaluated: {len(dataset_dict['question'])}")
    print(separator)

    print("\n📊 RETRIEVAL METRICS (Search Phase)")
    print(
        f"  Context Precision   : {fmt(scores.get('context_precision',  'N/A'))}"
        "  → Are relevant chunks ranked at top?"
    )
    print(
        f"  Context Recall      : {fmt(scores.get('context_recall',     'N/A'))}"
        "  → Did we retrieve all needed info?"
    )
    print(
        f"  Context Relevancy   : {fmt(scores.get('context_relevancy',  'N/A'))}"
        "  → Signal-to-noise ratio in retrieved chunks"
    )

    print("\n🤖 GENERATION METRICS (Response Phase)")
    print(
        f"  Faithfulness        : {fmt(scores.get('faithfulness',       'N/A'))}"
        "  → Anti-hallucination: claims traceable to context?"
    )
    print(
        f"  Answer Relevancy    : {fmt(scores.get('answer_relevancy',   'N/A'))}"
        "  → Does answer address the question?"
    )
    print(
        f"  Answer Correctness  : {fmt(scores.get('answer_correctness', 'N/A'))}"
        "  → Semantic match vs ground truth"
    )

    if category_scores:
        print("\n📁 CATEGORY BREAKDOWN")
        for cat, metrics in sorted(category_scores.items()):
            print(f"\n  [{cat}]")
            for metric, vals in metrics.items():
                avg = sum(vals) / len(vals)
                print(f"    {metric:<25} {avg:.3f}  (n={len(vals)})")

    print(f"\n{separator}\n")

    # ── Save JSON ──────────────────────────────────────────────────────────
    json_path = f"{RESULTS_DIR}/ragas_{timestamp}.json"
    output = {
        "timestamp": timestamp,
        "model": MODEL,
        "samples_evaluated": len(dataset_dict["question"]),
        "overall_scores": {k: round(float(v), 4) for k, v in scores.items()},
        "category_breakdown": {
            cat: {
                metric: round(sum(vals) / len(vals), 4)
                for metric, vals in metrics.items()
            }
            for cat, metrics in category_scores.items()
        },
        "per_question_results": (
            df.to_dict(orient="records") if "question" in df.columns else []
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info("JSON results saved: %s", json_path)

    # ── Save human-readable TXT ────────────────────────────────────────────
    txt_path = f"{RESULTS_DIR}/ragas_{timestamp}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Project Aegis — RAGAS Evaluation\n")
        f.write(f"Run: {timestamp}\n")
        f.write(f"Samples: {len(dataset_dict['question'])}\n\n")
        f.write("OVERALL SCORES\n")
        for metric, val in scores.items():
            try:
                f.write(f"  {metric:<30} {float(val):.4f}\n")
            except (ValueError, TypeError):
                f.write(f"  {metric:<30} N/A\n")
        if category_scores:
            f.write("\nCATEGORY BREAKDOWN\n")
            for cat, metrics in sorted(category_scores.items()):
                f.write(f"\n[{cat}]\n")
                for metric, vals in metrics.items():
                    f.write(
                        f"  {metric:<30} {sum(vals)/len(vals):.4f}  (n={len(vals)})\n"
                    )

    logger.info("TXT results saved: %s", txt_path)
    return json_path, txt_path, scores


def main():
    # ── 0. Validate ground truth exists ──────────────────────────────────
    if not os.path.exists(GROUND_TRUTH_PATH):
        logger.error(
            "Ground truth not found at %s\n"
            "Run first:  python -m eval.generate_ground_truth",
            GROUND_TRUTH_PATH,
        )
        return

    # ── 1. Load ground truth ──────────────────────────────────────────────
    samples = load_ground_truth(GROUND_TRUTH_PATH)
    if MAX_SAMPLES:
        samples = samples[:MAX_SAMPLES]
        logger.info("Capped to %d samples (MAX_SAMPLES=%d)", len(samples), MAX_SAMPLES)

    # ── 2. Build pipeline clients ─────────────────────────────────────────
    logger.info("\n=== Initialising Aegis pipeline ===")
    qdrant, openai_client, llm = build_pipeline_clients()

    # ── 3. Run pipeline on every sample ──────────────────────────────────
    logger.info("\n=== Running Aegis pipeline on %d samples ===", len(samples))
    dataset_dict = build_ragas_dataset(samples, qdrant, openai_client, llm)

    if not dataset_dict["question"]:
        logger.error(
            "No samples succeeded. Check your .env credentials and Qdrant connection."
        )
        return

    # ── 4. Run RAGAS ──────────────────────────────────────────────────────
    ragas_results = run_ragas_evaluation(dataset_dict)

    # ── 5. Format + save ──────────────────────────────────────────────────
    json_path, txt_path, scores = format_and_save_results(
        ragas_results, dataset_dict, samples
    )

    print(f"Results saved:\n  JSON → {json_path}\n  TXT  → {txt_path}")


if __name__ == "__main__":
    main()
