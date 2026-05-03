# retrieval/filters.py
import logging
from collections import defaultdict
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ingestion.embedder import get_embedding, COLLECTION_NAME

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
    # ── END DEFENSIVE PARSING ─────────────────────────────────────────────────


def pre_filter_search(query: str, qdrant: QdrantClient, openai_client: OpenAI, llm, top_k: int = 5) -> list:
    # Step 1: detect category
    category = detect_category(query, llm)

    # Step 2: embed query
    query_vector = get_embedding(query, openai_client)

    # Step 3: build filter if category found
    query_filter = None
    if category is not None:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="policy_category",
                    match=MatchValue(value=category)
                )
            ]
        )

    # Step 4: search Qdrant with or without filter
    results = qdrant.query_points(  # type: ignore
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k
    ).points

    # Step 5: format results
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


def post_filter_by_date(results: list) -> list:
    """
    Keep only chunks from the most recent version of each document.
    Groups by document_id, finds the latest effective_date per document,
    then keeps ALL chunks from that latest version.
    This fixes the bug where only 1 chunk per document was kept,
    causing the correct answer chunk to be dropped.
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
