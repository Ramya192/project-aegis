# retrieval/retriever.py
import logging
import re
from openai import OpenAI
from qdrant_client import QdrantClient
from ingestion.embedder import get_embedding, COLLECTION_NAME
from collections import defaultdict

logger = logging.getLogger(__name__)

# Regex to strip leading numbering like "1.", "1)", "- ", "* " from query lines
_NUMBERING_RE = re.compile(r"^\s*(\d+[\.\)]\s*|[-*•]\s*)")

# Phrases that indicate the LLM added a preamble line instead of a query
_PREAMBLE_PHRASES = [
    "here are", "alternative", "search quer", "following", "below",
    "sure", "certainly", "variations", "rephrased"
]


def basic_search(query, qdrant, openai_client, top_k=5):
    # Step 1: embed the query
    query_vector = get_embedding(query, openai_client)

    # Step 2: search Qdrant
    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    ).points

    # Step 3: format results
    response = []
    for hit in results:
        if hit.payload is None:
            continue
        response.append({
            "id": hit.id,
            "score": hit.score,
            "text": hit.payload.get("chunk_text", ""),
            "metadata": hit.payload
        })

    return response


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
    all_queries = [query] + clean_queries
    all_queries = list(dict.fromkeys(all_queries))

    logger.debug("generate_multi_queries: final query list: %s", all_queries)
    return all_queries
    # ── END DEFENSIVE PARSING ─────────────────────────────────────────────────


def multi_query_search(query: str, qdrant: QdrantClient, openai_client: OpenAI, llm, top_k: int = 5) -> list:

    # Step 1: generate multiple queries
    queries = generate_multi_queries(query, llm)

    # Step 2: search Qdrant for each query
    all_ranked_lists = []
    for q in queries:
        results = basic_search(q, qdrant, openai_client, top_k=10)

        # Add rank to each result
        for rank, item in enumerate(results, start=1):
            item["rank"] = rank

        all_ranked_lists.append(results)

    # Step 3: RRF fusion
    doc_store = {}
    rrf_scores = defaultdict(float)
    k = 60

    for ranked_list in all_ranked_lists:
        for item in ranked_list:
            doc_id = item["id"]
            rank = item["rank"]
            doc_store[doc_id] = item
            rrf_scores[doc_id] += 1 / (k + rank)

    # Step 4: sort by fused score and return top_k
    fused = sorted(doc_store.keys(), key=lambda x: rrf_scores[x], reverse=True)
    return [doc_store[doc_id] for doc_id in fused[:top_k]]
