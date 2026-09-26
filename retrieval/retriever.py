# retrieval/retriever.py
import logging
import re
from collections import defaultdict

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
from ingestion.embedder import COLLECTION_NAME

logger = logging.getLogger(__name__)

# Regex to strip leading numbering like "1.", "1)", "- ", "* " from query lines
_NUMBERING_RE = re.compile(r"^\s*(\d+[\.\)]\s*|[-*•]\s*)")

# Phrases that indicate the LLM added a preamble line instead of a query
_PREAMBLE_PHRASES = [
    "here are", "alternative", "search quer", "following", "below",
    "sure", "certainly", "variations", "rephrased"
]


def vector_search(query_vector: list, qdrant: QdrantClient, top_k: int = 5,
                  category: list[str] | str | None = None) -> list:
    """Dense search in Qdrant, optionally restricted to one or more policy categories.

    The detected category may not exist in the corpus (e.g. the LLM says "Legal"
    but every chunk is tagged HR), so an empty filtered search is retried unfiltered.
    """
    query_filter = None
    if category:
        categories = [category] if isinstance(category, str) else list(category)
        match = MatchValue(value=categories[0]) if len(categories) == 1 else MatchAny(any=categories)
        query_filter = Filter(must=[FieldCondition(key="policy_category", match=match)])

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k
    ).points

    if not results and query_filter is not None:
        logger.warning(
            "vector_search: category '%s' matched no chunks — retrying without filter",
            category,
        )
        results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k
        ).points

    return [
        {
            "id": hit.id,
            "score": hit.score,
            "text": hit.payload.get("chunk_text", ""),
            "metadata": hit.payload
        }
        for hit in results
        if hit.payload is not None
    ]


def rrf_fuse(ranked_lists: list[list], limit: int, k: int = 60) -> list:
    """Reciprocal Rank Fusion: score each chunk by sum(1 / (k + rank)) across lists."""
    doc_store = {}
    rrf_scores = defaultdict(float)
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            doc_store[item["id"]] = item
            rrf_scores[item["id"]] += 1 / (k + rank)

    fused = sorted(doc_store, key=lambda doc_id: rrf_scores[doc_id], reverse=True)
    return [doc_store[doc_id] for doc_id in fused[:limit]]


def generate_multi_queries(query: str, llm, n: int = 3) -> list:
    prompt = f"""
    You are helping retrieve corporate policy information.
    Generate {n} short alternative search queries for the query below.
    Keep them close in meaning.
    Return only the queries, one per line.
    Do not number them. Do not add any introduction or explanation.

    User query: {query}
    """

    raw_text = llm.invoke(prompt).content.strip()

    # ── DEFENSIVE PARSING ────────────────────────────────────────────────────
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    clean_queries = []
    for line in lines:
        # 1. Drop preamble lines (e.g. "Here are 3 alternative queries:")
        line_lower = line.lower()
        if any(phrase in line_lower for phrase in _PREAMBLE_PHRASES):
            logger.debug("generate_multi_queries: skipping preamble line: '%s'", line)
            continue

        # 2. Strip leading numbering (e.g. "1. ", "2) ", "- ", "* ")
        clean = _NUMBERING_RE.sub("", line).strip()

        # 3. Skip if stripping left an empty string or a very short fragment
        if len(clean) < 5:
            logger.debug("generate_multi_queries: skipping too-short line: '%s'", line)
            continue

        clean_queries.append(clean)

    # 4. Fall back to original query if parsing produced nothing usable
    if not clean_queries:
        logger.warning(
            "generate_multi_queries: could not parse any variants from LLM output — "
            "falling back to original query only. Raw output: '%s'",
            raw_text
        )
        return [query]

    # 5. Combine original + variants, deduplicate, preserve order
    all_queries = list(dict.fromkeys([query] + clean_queries))

    logger.debug("generate_multi_queries: final query list: %s", all_queries)
    return all_queries
