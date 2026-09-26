# eval/run_retrieval_ablation.py
"""
Retrieval ablation: did the chunk holding each required fact reach the LLM?

Every question in ground_truth_hard.json and ground_truth_heldout.json lists "needles", short strings
that appear in the chunk holding a fact the answer needs. For each question the real pipeline is run
and each needle is looked for in the chunks sent to the LLM. This measures retrieval directly, so it is
steadier than scoring LLM answers, which vary from run to run.

Compare pipeline settings with the environment variables the pipeline reads:

    AEGIS_MAX_CATEGORIES=1 AEGIS_CONTEXT_CHUNKS=5 python -m eval.run_retrieval_ablation old_settings
    AEGIS_MAX_CATEGORIES=2 AEGIS_CONTEXT_CHUNKS=8 python -m eval.run_retrieval_ablation new_settings

Usage:
    python -m eval.run_retrieval_ablation <label> [repeats]
"""

import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from eval.run_ragas_eval import RESULTS_DIR, build_pipeline_clients, run_pipeline_for_sample

SETS = ("eval/ground_truth_hard.json", "eval/ground_truth_heldout.json")
# "three (3) business days" also appears in an unrelated chunk, so use the specific phrase
SPECIFIC = {"three (3) business days": "return all corporate hardware"}


class FallbackCounter(logging.Handler):
    """Counts Cohere failures: a run that silently fell back to another reranker is not valid."""

    count = 0

    def emit(self, record):
        message = record.getMessage()
        if "falling back" in message or "unavailable" in message:
            FallbackCounter.count += 1


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    logging.getLogger("retrieval.reranker").addHandler(FallbackCounter())
    for noisy in ("httpx", "httpcore", "openai", "qdrant_client"):
        logging.getLogger(noisy).setLevel(logging.ERROR)

    items = []
    for path in SETS:
        with open(path, encoding="utf-8") as f:
            items += [i for i in json.load(f) if i.get("needles")]

    qdrant, openai_client, llm = build_pipeline_clients()
    rows = []
    for item in items:
        needles = [SPECIFIC.get(n, n) for n in item["needles"]]
        runs = []
        for _ in range(repeats):
            result = run_pipeline_for_sample(item["question"], qdrant, openai_client, llm)
            hits = [any(n in c for c in result["contexts"]) for n in needles]
            runs.append({"hits": hits, "chunks": len(result["contexts"]),
                         "category": result["category_detected"], "answer": result["answer"]})
        rows.append({"id": item["id"], "type": item["category"], "needles": needles, "runs": runs})
        share = sum(sum(r["hits"]) for r in runs) / (len(needles) * repeats)
        print(f"{item['id']:3} needed facts present {share:4.0%}  categories={sorted({str(r['category']) for r in runs})}", flush=True)

    total = sum(len(r["needles"]) * repeats for r in rows)
    found = sum(sum(x["hits"]) for r in rows for x in r["runs"])
    complete = sum(all(x["hits"]) for r in rows for x in r["runs"])
    held = [r for r in rows if r["id"].startswith("H")]
    held_total = sum(len(r["needles"]) * repeats for r in held)
    held_found = sum(sum(x["hits"]) for r in held for x in r["runs"])
    print(f"\nCohere fallbacks: {FallbackCounter.count} (must be 0 for a valid run)")
    print(f"[{label}] needed facts present {found}/{total} = {found / total:.0%} | "
          f"questions with every fact present {complete}/{len(rows) * repeats} | "
          f"held-out questions only {held_found}/{held_total} = {held_found / held_total:.0%}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = f"{RESULTS_DIR}/ablation_{label}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"label": label, "repeats": repeats, "fallbacks": FallbackCounter.count, "rows": rows}, f, indent=1)
    print("saved", out)


if __name__ == "__main__":
    main()
