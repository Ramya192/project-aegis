# retrieval/filters.py
import logging
from collections import defaultdict
from openai import OpenAI
from qdrant_client import QdrantClient
from ingestion.embedder import get_embedding
from retrieval.retriever import vector_search

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["Travel", "HR", "Finance", "IT", "Legal", "Compliance", "Other"]


def detect_category(query: str, llm) -> str | None:
    prompt = f"""
    You are a corporate policy classifier.
    Classify the query below into ONE of these categories:
    - Travel: questions about flights, hotels, taxis, transport, per diems, travel expenses, mileage reimbursement, expense reports, trip approvals, rental cars
    - HR: questions about leave, salary, performance, conduct, training, learning stipends, tuition assistance, professional development budgets, PTO, parental leave
    - Finance: questions about corporate budgets, invoices, accounting, financial statements (NOT travel expenses or employee reimbursements)
    - IT: questions about security, data, systems, software
    - Legal: questions about contracts, compliance, regulations
    - Compliance: questions about audits, policies, governance
    - Other: anything else

    If unsure, return None.
    Return ONLY the category name or None. No explanation.

    Query: {query}
    """

    raw = llm.invoke(prompt).content.strip()

    # ── DEFENSIVE PARSING ────────────────────────────────────────────────────
    # The LLM might return "Travel policy", "travel", "The category is Travel",
    # or add quotes/punctuation. We try to extract a valid category from the
    # response rather than requiring an exact match.

    # 1. Exact match first (happy path)
    if raw in VALID_CATEGORIES:
        return raw

    # 2. Case-insensitive match
    raw_lower = raw.lower()
    for cat in VALID_CATEGORIES:
        if cat.lower() == raw_lower:
            logger.debug("detect_category: case-insensitive match '%s' → '%s'", raw, cat)
            return cat

    # 3. Category name appears anywhere in the response (e.g. "The category is Travel")
    for cat in VALID_CATEGORIES:
        if cat.lower() in raw_lower:
            logger.warning(
                "detect_category: fuzzy match — LLM returned '%s', extracted '%s'",
                raw, cat
            )
            return cat

    # 4. Nothing matched — fall back to None (no pre-filter applied)
    logger.warning(
        "detect_category: could not parse '%s' — falling back to None (no category filter)",
        raw
    )
    return None


def pre_filter_search(query: str, qdrant: QdrantClient, openai_client: OpenAI,
                      category: str | None, top_k: int = 5) -> list:
    """Embed the query and search Qdrant, restricted to the detected category if any."""
    query_vector = get_embedding(query, openai_client)
    return vector_search(query_vector, qdrant, top_k=top_k, category=category)


def post_filter_by_date(results: list) -> list:
    """
    Keep only chunks from the most recent version of each document.
    Groups by document_id, finds the latest effective_date per document,
    then keeps ALL chunks from that latest version (not just one chunk per
    document, which would drop the chunk that actually answers the question).
    """
    # Step 1: group all chunks by document_id
    doc_groups = defaultdict(list)
    for item in results:
        doc_id = item["metadata"].get("document_id", "unknown")
        doc_groups[doc_id].append(item)

    filtered = []
    for doc_id, chunks in doc_groups.items():
        # Step 2: find the most recent effective_date for this document
        latest_date = max(
            chunk["metadata"].get("effective_date") or "0000-01-01"
            for chunk in chunks
        )

        # Step 3: keep ALL chunks that match the latest date
        latest_chunks = [
            chunk for chunk in chunks
            if (chunk["metadata"].get("effective_date") or "0000-01-01") == latest_date
        ]
        filtered.extend(latest_chunks)

    return filtered
