# api.py

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr
from openai import OpenAI
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI

from chat import ask

app = FastAPI(title="Project Aegis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Clients (initialised once at startup) ---
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
qdrant_client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
    timeout=60
)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=SecretStr(os.environ["OPENAI_API_KEY"])
)


class QueryRequest(BaseModel):
    query: str
    session_id: str = "default_session"


class ChunkInfo(BaseModel):
    document_id: str
    section: str
    score: float
    text_preview: str


class QueryResponse(BaseModel):
    answer: str
    category_detected: str | None
    sources: list[ChunkInfo]
    concepts_used: list[str]


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    result = ask(
        query=request.query,
        session_id=request.session_id,
        qdrant=qdrant_client,
        openai_client=openai_client,
        llm=llm
    )

    # Format sources
    sources = []
    for chunk in result["sources"]:
        raw_score = float(chunk.get("rerank_score", 0))
        sources.append(ChunkInfo(
            document_id=chunk["metadata"].get("document_id", "Unknown"),
            section=chunk["metadata"].get("h2_header", ""),
            score=round(raw_score, 4),
            text_preview=chunk["text"][:400]
        ))

    concepts = [
        "Multi-Query Expansion",
        "HyDE",
        "Metadata Pre-Filter",
        "RRF Fusion",
        "Post-Filter by Date",
        "Cross-Encoder Reranking",
    ]

    return QueryResponse(
        answer=result["answer"],
        category_detected=result["category_detected"],
        sources=sources,
        concepts_used=concepts
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": "gpt-4o-mini"}
