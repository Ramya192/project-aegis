import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import numpy as np
from sentence_transformers import CrossEncoder

# Load once when module is imported
_rerank_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    model_kwargs={"cache_dir": "./models/cache"}
)

def rerank(query: str, chunks: list, top_k: int = 5) -> list:

    # Step 1: create [query, chunk_text] pairs
    pairs = [[query, chunk["text"]] for chunk in chunks]

    # Step 2: score all pairs at once
    raw_scores = _rerank_model.predict(pairs)
    # Min-max normalize to 0-1 range across the batch
    min_s, max_s = raw_scores.min(), raw_scores.max()
    if max_s > min_s:
        scores = (raw_scores - min_s) / (max_s - min_s)
    else:
        scores = raw_scores

    # Step 3: attach score to each chunk
    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = scores[i]

    # Step 4: sort by rerank_score descending
    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    # Step 5: return top_k
    return reranked[:top_k]