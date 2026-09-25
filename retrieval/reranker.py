# retrieval/reranker.py
# Uses the Cohere Rerank API when COHERE_API_KEY is set (the deployed app — no torch needed).
# Falls back to a local CrossEncoder otherwise (requires requirements-dev.txt).

import logging
import os

import numpy as np

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

logger = logging.getLogger(__name__)

COHERE_MODEL = "rerank-english-v3.0"

# Cohere relevance scores are absolute (0-1), so chunks scoring below this are dropped
# instead of being padded into the context up to top_k. The best chunk is always kept.
# (The local CrossEncoder's scores are min-max scaled per query, so no cutoff applies there.)
MIN_COHERE_RELEVANCE = 0.1
CROSSENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_rerank_model = None
_cohere_client = None


def get_cohere_client():
    global _cohere_client
    if _cohere_client is None:
        import cohere
        _cohere_client = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
        logger.info("Cohere Rerank client loaded.")
    return _cohere_client


def get_reranker():
    """Load the local CrossEncoder (used when no COHERE_API_KEY is set)."""
    global _rerank_model
    if _rerank_model is None:
        from sentence_transformers import CrossEncoder
        _rerank_model = CrossEncoder(
            CROSSENCODER_MODEL,
            model_kwargs={"cache_dir": "./models/cache"}
        )
        logger.info("CrossEncoder loaded.")
    return _rerank_model


def _cohere_rerank(query: str, chunks: list, top_k: int) -> list:
    """Rerank with the Cohere API. relevance_score is already in [0, 1]."""
    response = get_cohere_client().rerank(
        model=COHERE_MODEL,
        query=query,
        documents=[chunk["text"] for chunk in chunks],
        top_n=top_k,
    )

    # Results come back best-first; keep the top one even if it scores below the cutoff.
    results = [r for r in response.results if r.relevance_score >= MIN_COHERE_RELEVANCE]
    results = results or response.results[:1]

    reranked = []
    for result in results:
        chunk = chunks[result.index]
        chunk["rerank_score"] = round(float(result.relevance_score), 4)
        reranked.append(chunk)
    return reranked


def _crossencoder_rerank(query: str, chunks: list, top_k: int) -> list:
    """Rerank with the local CrossEncoder; raw logits are min-max scaled to [0, 1]."""
    model = get_reranker()
    raw_scores = model.predict([[query, chunk["text"]] for chunk in chunks])

    if len(raw_scores) > 1:
        mn, mx = raw_scores.min(), raw_scores.max()
        scores = (raw_scores - mn) / (mx - mn) if mx > mn else np.ones_like(raw_scores)
    else:
        scores = np.array([1.0])

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    return sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)[:top_k]


def _fallback_order(chunks: list, top_k: int) -> list:
    """Keep the incoming RRF order; the vector-similarity score stands in as rerank_score."""
    for chunk in chunks:
        chunk["rerank_score"] = float(chunk.get("score", 0))
    return chunks[:top_k]


def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    if not chunks:  # Cohere rejects an empty document list with a 400
        return []
    if os.getenv("COHERE_API_KEY"):
        try:
            return _cohere_rerank(query, chunks, top_k)
        except Exception as e:  # rate limit, outage, bad key — answer anyway
            logger.warning("Cohere rerank failed (%s) — falling back", e)
    try:
        return _crossencoder_rerank(query, chunks, top_k)
    except ImportError:  # deployed image has no sentence-transformers
        logger.warning("CrossEncoder unavailable — keeping RRF order without reranking")
        return _fallback_order(chunks, top_k)
