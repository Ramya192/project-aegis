# retrieval/filters.py
import logging
import os
import re
from collections import defaultdict
from openai import OpenAI
from qdrant_client import QdrantClient
from ingestion.embedder import get_embedding
from retrieval.retriever import vector_search

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["Travel", "HR", "Finance", "IT", "Legal", "Compliance", "Other"]

# A question can span two policy areas (e.g. an L&D stipend question that also needs the travel
# hotel limit), so the classifier may return up to this many categories. 1 restores the old
# single-category behaviour (the AEGIS_MAX_CATEGORIES environment variable exists for ablations).
MAX_CATEGORIES = int(os.getenv("AEGIS_MAX_CATEGORIES", "2"))

_CANONICAL = {c.lower(): c for c in VALID_CATEGORIES}


def _parse_categories(raw: str) -> list[str]:
    """Extract valid category names, in order of appearance and without repeats."""
    # 1. Happy path: a comma/plus/"and"-separated list where every item is a valid category
    tokens = [t.strip(" \t\n\"'.`*") for t in re.split(r"[,/&+]|\band\b", raw, flags=re.I)]
    tokens = [t for t in tokens if t]
    if tokens and all(t.lower() in _CANONICAL for t in tokens):
        return list(dict.fromkeys(_CANONICAL[t.lower()] for t in tokens))

    # 2. Category names appear inside a sentence (e.g. "The category is Travel").
    #    Word boundaries stop "it" or "hr" matching inside other words; "IT" must be upper-case
    #    so the pronoun "it" is not read as the IT category.
    found = []
    for m in re.finditer(r"\b(" + "|".join(map(re.escape, VALID_CATEGORIES)) + r")\b", raw, flags=re.I):
        word = m.group(1)
        if word.lower() == "it" and word != "IT":
            continue
        cat = _CANONICAL[word.lower()]
        if cat not in found:
            found.append(cat)
    return found


def detect_category(query: str, llm) -> list[str] | None:
    """Classify the query into 1..MAX_CATEGORIES policy categories, or None (no filter)."""
    if MAX_CATEGORIES > 1:
        how_many = (
            "Classify the query below into ONE of these categories, or into TWO if answering it clearly\n"
            "    needs information from two different categories (for example a learning stipend question that also\n"
            "    asks about hotel rates needs HR and Travel):"
        )
        answer_format = "Return ONLY the category name(s), separated by a comma (at most two). No explanation."
    else:
        how_many = "Classify the query below into ONE of these categories:"
        answer_format = "Return ONLY the category name or None. No explanation."

    prompt = f"""
    You are a corporate policy classifier.
    {how_many}
    - Travel: questions about flights, hotels, taxis, transport, per diems, travel expenses, mileage reimbursement, expense reports, trip approvals, rental cars
    - HR: questions about leave, salary, performance, conduct, training, learning stipends, tuition assistance, professional development budgets, PTO, parental leave
    - Finance: questions about corporate budgets, invoices, accounting, financial statements (NOT travel expenses or employee reimbursements)
    - IT: questions about security, data, systems, software
    - Legal: questions about contracts, compliance, regulations
    - Compliance: questions about audits, policies, governance
    - Other: anything else

    If unsure, return None.
    {answer_format}

    Query: {query}
    """

    raw = llm.invoke(prompt).content.strip()

    # ── DEFENSIVE PARSING ────────────────────────────────────────────────────
    # The LLM might return "Travel policy", "travel", "HR, Travel", "The category is Travel",
    # or add quotes/punctuation, so extract valid category names instead of requiring an exact match.
    categories = _parse_categories(raw)[:MAX_CATEGORIES]
    if categories:
        return categories

    # Nothing matched — fall back to None (no pre-filter applied)
    logger.warning(
        "detect_category: could not parse '%s' — falling back to None (no category filter)",
        raw
    )
    return None


def pre_filter_search(query: str, qdrant: QdrantClient, openai_client: OpenAI,
                      category: list[str] | str | None, top_k: int = 5) -> list:
    """Embed the query and search Qdrant, restricted to the detected categories if any."""
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
