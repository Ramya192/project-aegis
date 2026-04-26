from collections import defaultdict
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ingestion.embedder import get_embedding, COLLECTION_NAME

def detect_category(query:str, llm) -> str | None:
    prompt = f"""
    You are a corporate policy classifier.
    Classify the query below into ONE of these categories:
    - Travel: questions about flights, hotels, taxis, transport, per diems, travel expenses
    - HR: questions about leave, salary, performance, conduct, training
    - Finance: questions about budgets, invoices, accounting
    - IT: questions about security, data, systems, software
    - Legal: questions about contracts, compliance, regulations
    - Compliance: questions about audits, policies, governance
    - Other: anything else

    If unsure, return None.
    Return ONLY the category name or None. No explanation.

    Query: {query}
    """

    result = llm.invoke(prompt).content.strip()
    valid = ["Travel", "HR", "Finance", "IT", "Legal", "Compliance", "Other"]

    if result in valid:
        return result
    return None
    
def pre_filter_search(query:str, qdrant: QdrantClient, openai_client:OpenAI, llm, top_k:int=5) -> list:
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
    results = qdrant.query_points( # type: ignore
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
    doc_groups = defaultdict(list)

    for item in results:
        doc_id = item["metadata"].get("document_id", "unknown")
        doc_groups[doc_id].append(item)

    filtered = []
    for doc_id, chunks in doc_groups.items():
        chunks.sort(
            key=lambda x: x["metadata"].get("effective_date") or "0000-01-01",
            reverse=True
        )
        filtered.append(chunks[0])

    return filtered
