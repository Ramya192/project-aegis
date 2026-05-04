# api.py  -- lazy-loaded version for Render free tier (512MB RAM)

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, SecretStr

app = FastAPI(title="Project Aegis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Globals — initialised at startup ────────────────────────
_openai_client = None
_qdrant_client = None
_llm           = None

def get_clients():
    return _openai_client, _qdrant_client, _llm


def _init_all():
    """Load all clients and models synchronously at module import time.
    Runs before uvicorn accepts any requests — safe from the 30s timeout.
    """
    global _openai_client, _qdrant_client, _llm

    print("==> Loading OpenAI client...", flush=True)
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    print("==> Loading Qdrant client...", flush=True)
    from qdrant_client import QdrantClient
    _qdrant_client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        timeout=60,
    )

    print("==> Loading LangChain LLM...", flush=True)
    from langchain_openai import ChatOpenAI
    _llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )

    print("==> Warming up CrossEncoder reranker...", flush=True)
    from chat import preload_reranker
    preload_reranker()

    print("==> All models loaded — ready to serve requests.", flush=True)

# Run at import time — before uvicorn starts accepting connections
_init_all()


# ── Pydantic models ──────────────────────────────────────────
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


# ── Routes ───────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": "gpt-4o-mini"}


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    from chat import ask   # also lazy — imports sentence-transformers only on first call

    openai_client, qdrant_client, llm = get_clients()

    result = ask(
        query=request.query,
        session_id=request.session_id,
        qdrant=qdrant_client,
        openai_client=openai_client,
        llm=llm,
    )

    sources = []
    for chunk in result["sources"]:
        sources.append(ChunkInfo(
            document_id=chunk.get("document_id", "Unknown"),
            section=chunk.get("section", ""),
            score=round(float(chunk.get("score", 0)), 4),
            text_preview=chunk.get("text_preview", "")[:400],
        ))

    concepts = [
        "Multi-Query Expansion", "HyDE", "Metadata Pre-Filter",
        "RRF Fusion", "Post-Filter by Date", "Cross-Encoder Reranking",
    ]

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
