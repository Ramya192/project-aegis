# retrieval/reranker.py
# Uses CrossEncoder locally, falls back to BM25 on Render (no model download needed)

import os
import numpy as np

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

_rerank_model = None
_USE_CROSSENCODER = os.getenv("USE_CROSSENCODER", "true").lower() == "true"


def get_reranker():
    global _rerank_model
    if _rerank_model is None and _USE_CROSSENCODER:
        try:
            from sentence_transformers import CrossEncoder
            _rerank_model = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                model_kwargs={"cache_dir": "./models/cache"}
            )
            print("==> CrossEncoder loaded.", flush=True)
        except Exception as e:
            print(f"==> CrossEncoder failed to load: {e}. Falling back to BM25.", flush=True)
            _rerank_model = None
    return _rerank_model


def _bm25_rerank(query: str, chunks: list, top_k: int) -> list:
    """Lightweight BM25-style reranking — no model needed."""
    from collections import Counter
    import math

    query_terms = query.lower().split()
    scores = []

    for chunk in chunks:
        text = chunk["text"].lower()
        words = text.split()
        word_count = len(words) + 1
        tf_scores = Counter(words)

        score = 0.0
        for term in query_terms:
            tf = tf_scores.get(term, 0)
            # BM25 formula: TF * IDF approximation
            score += (tf * 2.5) / (tf + 1.5 * (1 - 0.75 + 0.75 * word_count / 150))

        scores.append(score)

    # Normalize 0-1
    max_s = max(scores) if scores else 1
    min_s = min(scores) if scores else 0
    rng = max_s - min_s if max_s != min_s else 1

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = round((scores[i] - min_s) / rng, 4)

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]


def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    model = get_reranker()

    if model is None:
        # No CrossEncoder available — use BM25
        print("==> Using BM25 reranking.", flush=True)
        return _bm25_rerank(query, chunks, top_k)

    # CrossEncoder path
    pairs = [[query, chunk["text"]] for chunk in chunks]
    raw_scores = model.predict(pairs)

    if len(raw_scores) > 1:
        mn, mx = raw_scores.min(), raw_scores.max()
        scores = (raw_scores - mn) / (mx - mn) if mx > mn else np.ones_like(raw_scores)
    else:
        scores = np.array([1.0])

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]
