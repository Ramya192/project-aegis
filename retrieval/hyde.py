# retrieval/hyde.py
from openai import OpenAI
from qdrant_client import QdrantClient
from ingestion.embedder import get_embedding
from retrieval.retriever import vector_search


def generate_hypothetical_answer(query: str, llm) -> str:
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
    """Embed an LLM-written hypothetical answer and search with it instead of the query."""
    hypothetical_answer = generate_hypothetical_answer(query, llm)
    query_vector = get_embedding(hypothetical_answer, openai_client)
    return vector_search(query_vector, qdrant, top_k=top_k, category=category)
