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


class TokenInfo(BaseModel):
    total_tokens_before: int
    total_tokens_after: int
    chunks_before: int
    chunks_after: int
    truncated: bool
    dropped_chunks: int
    budget: int


class QueryResponse(BaseModel):
    answer: str
    category_detected: str | None
    sources: list[ChunkInfo]
    concepts_used: list[str]
    token_info: TokenInfo | None = None


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    result = ask(
        query=request.query,
        session_id=request.session_id,
        qdrant=qdrant_client,
        openai_client=openai_client,
        llm=llm
    )

    # FIX: chat.py now returns sources as flat dicts — read keys directly
    # Old format: chunk["metadata"]["document_id"], chunk["text"]
    # New format: chunk["document_id"], chunk["text_preview"]
    sources = []
    for chunk in result["sources"]:
        sources.append(ChunkInfo(
            document_id=chunk.get("document_id", "Unknown"),
            section=chunk.get("section", ""),
            score=round(float(chunk.get("score", 0)), 4),
            text_preview=chunk.get("text_preview", "")[:400]
        ))

    concepts = [
        "Multi-Query Expansion",
        "HyDE",
        "Metadata Pre-Filter",
        "RRF Fusion",
        "Post-Filter by Date",
        "Cross-Encoder Reranking",
    ]

    # token_info is optional — won't break if missing
    token_info = None
    if result.get("token_info"):
        ti = result["token_info"]
        token_info = TokenInfo(
            total_tokens_before=ti.get("total_tokens_before", 0),
            total_tokens_after=ti.get("total_tokens_after", 0),
            chunks_before=ti.get("chunks_before", 0),
            chunks_after=ti.get("chunks_after", 0),
            truncated=ti.get("truncated", False),
            dropped_chunks=ti.get("dropped_chunks", 0),
            budget=ti.get("budget", 3000),
        )

    return QueryResponse(
        answer=result["answer"],
        category_detected=result.get("category_detected"),
        sources=sources,
        concepts_used=concepts,
        token_info=token_info,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": "gpt-4o-mini"}
