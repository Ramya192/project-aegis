# retrieval/reranker.py — lazy-load CrossEncoder to avoid startup OOM on Render

import os
import numpy as np
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

_rerank_model = None  # not loaded at import time

def get_reranker():
    """Load CrossEncoder once and cache it."""
    global _rerank_model
    if _rerank_model is None:
        from sentence_transformers import CrossEncoder
        _rerank_model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            model_kwargs={"cache_dir": "./models/cache"}
        )
    return _rerank_model


def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    model = get_reranker()
    pairs = [[query, chunk["text"]] for chunk in chunks]
    raw_scores = model.predict(pairs)

    if len(raw_scores) > 1:
        mn, mx = raw_scores.min(), raw_scores.max()
        if mx > mn:
            scores = (raw_scores - mn) / (mx - mn)
        else:
            scores = np.ones_like(raw_scores)
    else:
        scores = np.array([1.0])

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]
