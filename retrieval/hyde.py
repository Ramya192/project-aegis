from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from ingestion.embedder import get_embedding, COLLECTION_NAME

def generate_hypothetical_answer(query:str,llm) -> str:
    prompt = f"""
    You are a corporate policy assistant.
    Write a short hypothetical answer for the question below.
    Write it as if it were extracted from a real policy document.
    Keep it under 100 words.
    Do not say 'hypothetical' or 'I dont know'.

    Question:{query}

    Answer:
    """
    return llm.invoke(prompt).content.strip()

def hyde_search(query: str, qdrant: QdrantClient, openai_client: OpenAI, llm,
                top_k: int = 5, category: str | None = None) -> list:

    # Step 1: generate hypothetical answer
    hypothetical_answer = generate_hypothetical_answer(query, llm)

    # Step 2: embed the hypothetical answer
    query_vector = get_embedding(hypothetical_answer, openai_client)

    # Step 3: build category filter if provided
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

    # Step 4: search Qdrant
    results = qdrant.query_points(
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