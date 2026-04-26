import os
import numpy as np
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
from sentence_transformers import CrossEncoder

_rerank_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    model_kwargs={"cache_dir": "./models/cache"}
)

def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    pairs = [[query, chunk["text"]] for chunk in chunks]
    raw_scores = _rerank_model.predict(pairs)

    # Normalize only when multiple chunks exist
    if len(raw_scores) > 1:
        mn, mx = raw_scores.min(), raw_scores.max()
        if mx > mn:
            scores = (raw_scores - mn) / (mx - mn)
        else:
            scores = np.ones_like(raw_scores)
    else:
        scores = np.array([1.0])  # single chunk always gets score 1.0

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]