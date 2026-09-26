# eval/run_hard_eval.py
"""
Harder evaluation set: cross-document, paraphrased and unanswerable questions.

  Answerable questions (cross-document, paraphrase)
      -> scored with the same RAGAS metrics as the main benchmark.
  Unanswerable questions
      -> RAGAS has no reference answer to compare against, so each one is scored
         pass/fail: does the answer say the information is not in the policy
         documents instead of giving a figure?

Usage:
    python -m eval.run_hard_eval                                        # eval/ground_truth_hard.json
    python -m eval.run_hard_eval eval/ground_truth_heldout.json heldout  # another set + results prefix
"""

import json
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from eval.run_ragas_eval import (
    RESULTS_DIR,
    MODEL,
    build_pipeline_clients,
    build_ragas_dataset,
    format_and_save_results,
    run_pipeline_for_sample,
    run_ragas_evaluation,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)

HARD_PATH = "eval/ground_truth_hard.json"

JUDGE_PROMPT = """You are grading a policy assistant on a question that CANNOT be answered from its documents.

Question: {question}

Assistant's answer: {answer}

PASS if the answer clearly says the information is not available / could not be found in the
policy documents, and does not present a specific figure or rule as the answer.
FAIL if the answer states a specific figure, rule or entitlement as if it were the answer.

Reply with exactly one word: PASS or FAIL."""


def judge_unanswerable(question: str, answer: str) -> bool:
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    judge = ChatOpenAI(model=MODEL, api_key=SecretStr(os.environ["OPENAI_API_KEY"]))
    verdict = judge.invoke(JUDGE_PROMPT.format(question=question, answer=answer))
    return verdict.content.strip().upper().startswith("PASS")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else HARD_PATH
    prefix = sys.argv[2] if len(sys.argv) > 2 else "hard"
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    answerable = [i for i in items if i["ground_truth"]]
    unanswerable = [i for i in items if not i["ground_truth"]]
    logger.info("Loaded %d answerable + %d unanswerable questions", len(answerable), len(unanswerable))

    qdrant, openai_client, llm = build_pipeline_clients()

    # ── Answerable: RAGAS ────────────────────────────────────────────────
    dataset_dict = build_ragas_dataset(answerable, qdrant, openai_client, llm)
    ragas_results = run_ragas_evaluation(dataset_dict)
    json_path, txt_path, _ = format_and_save_results(
        ragas_results, dataset_dict, answerable, prefix=prefix
    )

    # ── Unanswerable: pass/fail ──────────────────────────────────────────
    verdicts = []
    for item in unanswerable:
        logger.info("Unanswerable: %s", item["question"])
        result = run_pipeline_for_sample(item["question"], qdrant, openai_client, llm)
        passed = (not result["error"]) and judge_unanswerable(item["question"], result["answer"])
        verdicts.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": result["answer"],
                "passed": passed,
                "error": result["error"],
            }
        )

    passed_count = sum(v["passed"] for v in verdicts)
    print(f"\nUnanswerable questions passed: {passed_count} / {len(verdicts)}")
    for v in verdicts:
        print(f"  [{'PASS' if v['passed'] else 'FAIL'}] {v['id']}: {v['answer'][:160]}")

    # Keep every answer so the run can be read qualitatively, not just scored
    answers = [
        {"question": q, "ground_truth": gt, "answer": a}
        for q, gt, a in zip(
            dataset_dict["question"], dataset_dict["ground_truth"], dataset_dict["answer"]
        )
    ]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"{RESULTS_DIR}/{prefix}_{stamp}_answers.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "unanswerable_passed": passed_count,
                "unanswerable_total": len(verdicts),
                "unanswerable": verdicts,
                "answerable": answers,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved:\n  {json_path}\n  {txt_path}\n  {out_path}")


if __name__ == "__main__":
    main()
