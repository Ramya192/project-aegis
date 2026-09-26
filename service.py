# service.py -- in-process query pipeline
# The Streamlit app calls run_query() directly, so the whole app deploys as a
# single Streamlit Community Cloud service with no separate API server.

import os
from functools import lru_cache

from dotenv import load_dotenv
load_dotenv()

from pydantic import SecretStr

CONCEPTS_USED = [
    "Multi-Query Expansion", "HyDE", "Metadata Pre-Filter",
    "RRF Fusion", "Post-Filter by Date", "Cross-Encoder Reranking",
]


@lru_cache(maxsize=1)
def get_clients():
    """Build the OpenAI / Qdrant / LLM clients once per process (lazy)."""
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from langchain_openai import ChatOpenAI

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    qdrant_client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        timeout=60,
    )
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )
    return openai_client, qdrant_client, llm


def run_query(query: str, session_id: str) -> dict:
    """Run the full retrieval + answer pipeline and return the UI-ready result."""
    from chat import ask

    openai_client, qdrant_client, llm = get_clients()
    result = ask(
        query=query,
        session_id=session_id,
        qdrant=qdrant_client,
        openai_client=openai_client,
        llm=llm,
    )

    sources = [
        {
            "document_id": chunk.get("document_id", "Unknown"),
            "section": chunk.get("section", ""),
            "score": round(float(chunk.get("score", 0)), 4),
            "text": chunk["text"],
            "used": chunk.get("used", False),
        }
        for chunk in result["sources"]
    ]

    return {
        "answer": result["answer"],
        "category_detected": result.get("category_detected"),
        "sources": sources,
        "concepts_used": CONCEPTS_USED,
        "token_info": result.get("token_info"),
    }


def clear_session(session_id: str) -> None:
    """Drop the server-side chat history for a UI session."""
    from chat import clear_session as _clear
    _clear(session_id)
