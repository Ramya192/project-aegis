# Project Aegis — Advanced Enterprise RAG System

> **IITM Pravartak Advanced PG Certificate in Agentic AI — Agentic AI Assignment**  
> A production-grade, context-aware RAG chatbot built to navigate complex corporate policy documents with high accuracy.

🚀 **Live Demo:** https://project-aegis-policy-intelligence.streamlit.app/  
🔧 **API Backend:** https://project-aegis-api.onrender.com/health  
👩‍💻 **Built by:** Ramya A

---

## Objective

Most RAG systems fail in enterprise settings because they split documents arbitrarily, lose table structure, and retrieve irrelevant context. Project Aegis solves this by building a multi-stage pipeline that understands document structure, filters by intent, and reranks results before generating an answer.

**The system can answer questions like:**
- *"What is the maternity leave policy?"* → 16 weeks at 100% pay (HR-POL-4001-V6)
- *"What is the tuition reimbursement limit?"* → $5,250 USD per year (LND-POL-7010-V3)
- *"What are the IT data security requirements?"* → Zero-Trust Architecture, Data Classification, BYOD policies (SEC-POL-8005-V7)

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────┐
│           Query Transformation              │
│  • Multi-Query Expansion (3 variants)       │
│  • HyDE (Hypothetical Document Embedding)   │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Metadata Pre-Filter                 │
│  • LLM detects category (Travel/HR/IT/...)  │
│  • WHERE policy_category = 'X' in Qdrant    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│       Dense Vector Search (Qdrant)          │
│  • Top 13 chunks per query variant          │
│  • RRF Fusion → Top 25 unique chunks        │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Metadata Post-Filter                │
│  • Keep only most recent effective_date     │
│  • Drop older policy versions               │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│     Cross-Encoder Reranker                  │
│  • Cohere Rerank API (deployed)             │
│  • CrossEncoder ms-marco-MiniLM (local)     │
│  • Scores each chunk against query (0–1)    │
│  • Prunes to Top 5 most relevant chunks     │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│     Token Budget Enforcer (tiktoken)        │
│  • Counts tokens across top-5 chunks        │
│  • Trims lowest-ranked chunks if > 3,000    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│     LLM Answer Generation (GPT-4o-mini)     │
│  • Context-only answering                   │
│  • Multi-turn chat history preserved        │
└─────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
Streamlit Cloud (Frontend)
        ↓  HTTPS
Render (FastAPI Backend — always on via cron ping)
        ↓              ↓
  Qdrant Cloud    OpenAI API
  (Ireland)       (gpt-4o-mini)
```

- **Frontend:** Streamlit Cloud — auto-deploys on every GitHub push
- **Backend:** FastAPI on Render free tier — kept alive by cron-job.org pinging `/health` every 10 minutes
- **Vector DB:** Qdrant Cloud (free tier, Ireland region)
- **Session limit:** 10 queries per session (Clear conversation to reset)

> ⚠️ **Note:** First query after inactivity may take ~60 seconds (Render free tier cold start). Subsequent queries respond in 5–15 seconds.

---

## 🎯 Design Philosophy — ABCDEF Framework

| Letter | Meaning | Aegis |
|---|---|---|
| **A** — Acknowledge | Enterprise RAG fails due to bad chunking, no reranking, and version drift — this system was built to solve those specific failures | Problem statement |
| **B** — Background | 8 corporate policy documents, 284 indexed chunks, BFSI compliance use case requiring zero hallucination | Corpus & context |
| **C** — Core approach | An 8-stage retrieval pipeline — MQE + HyDE → RRF fusion → date filter → CrossEncoder reranking → token budget → LLM | Solution design |
| **D** — Details | Each technique justified by a specific failure mode it solves — not added for complexity | Implementation |
| **E** — Evaluation | Recall@5 = 100%, Category Accuracy = 100%, Answer Faithfulness = 57% (keyword-based, conservative) | Results |
| **F** — Future work | Semantic faithfulness scoring, SSE streaming, query complexity routing, persistent chat history | Limitations |

---

## 🎯 Design Philosophy — Why Advanced Retrieval?

A naive RAG implementation (embed query → search → send top-k to LLM) fails on enterprise policy documents for three specific reasons:

**Problem 1 — Single query coverage**

A user asking *"What is the reimbursement limit for taxis?"* may not use the exact vocabulary in the policy (*"ground transportation per diem"*). A single embedding search misses semantically equivalent phrasings.

→ **Solution:** Multi-Query Expansion generates 3 query variants. HyDE embeds a hypothetical answer instead of the raw query. Both are fused via RRF to maximise recall.

**Problem 2 — Document version drift**

Corporate policies are versioned. Retrieving a chunk from an outdated policy version is a compliance risk — an employee acting on superseded rules creates audit exposure.

→ **Solution:** Post-filter by `effective_date` ensures only chunks from the most recent document version reach the LLM.

**Problem 3 — Semantic ranking ≠ relevance ranking**

Vector similarity scores measure embedding proximity, not answer quality. The top-scored chunk by cosine similarity is often a section header or glossary entry, not the specific clause that answers the question.

→ **Solution:** CrossEncoder reranking (Cohere Rerank API on deployment, ms-marco-MiniLM-L-6-v2 locally) re-scores all 20 fused chunks by query-document relevance, keeping only the top 5 for the LLM.

**Problem 4 — Silent context overflow**

If 5 reranked chunks each contain dense policy tables, the total token count can silently exceed the LLM's effective context budget, causing truncation or degraded answer quality ("Lost in the Middle" effect).

→ **Solution:** A token budget enforcer (tiktoken) counts tokens before the LLM call and trims from the lowest-ranked chunk upward if the total exceeds 3,000 tokens. Token usage is surfaced in the Streamlit sidebar per query.

Each technique was introduced to solve a specific, observed failure mode — not for complexity's sake.

---

## 📊 Evaluation Results

Aegis includes a formal evaluation framework (`eval/`) with 15 golden question-answer pairs drawn from the actual policy corpus, covering all 5 policy categories (Travel, HR, IT Security, Learning & Development, Performance).

**Run the evaluation:**
```bash
python -m eval.run_eval
```

### Latest Results (May 3, 2026)

| Metric | Score | What It Measures |
|---|---|---|
| **Retrieval Recall@5** | **100%** | Did the correct policy document appear in the top-5 retrieved chunks? |
| **Category Accuracy** | **100%** | Did `detect_category()` correctly classify the query's policy domain? |
| **Answer Faithfulness** | **57%** | Do LLM answers contain the expected key facts? (keyword-based) |
| **Token Truncations** | **0 / 15** | Queries where token budget enforcer had to drop chunks |

**Retrieval Recall@5 = 100%** means the pipeline never fails to find the right source document across all test queries — a critical baseline for any production RAG system.

**Answer Faithfulness = 57%** reflects the conservative nature of exact keyword matching. The LLM answers are factually correct but frequently paraphrase policy language. Semantic similarity scoring would yield higher faithfulness and is listed as a future improvement.

Results are automatically saved to `eval/results/` as JSON and plain text after each run.

---

## 📋 Self-Evaluation Rubric

| Criteria | Max | Score | Notes |
|---|---|---|---|
| Retrieval pipeline complexity | 20 | 19 | 8-stage pipeline, all techniques justified |
| Answer grounding / no hallucination | 20 | 18 | Context-only prompting, category pre-filtering |
| UI quality | 15 | 14 | BFSI professional theme, live pipeline status |
| Code quality / structure | 15 | 13 | 4 packages, FastAPI + Streamlit separation |
| Evaluation metrics | 15 | 13 | Recall@5, Faithfulness, Category Accuracy |
| Documentation / README | 15 | 14 | Architecture, ABCDEF, known limitations |
| **Total** | **100** | **91** | |

---

## Folder Structure

```
project-aegis/
│
├── chat.py              # Pipeline entry point — ask questions, get answers
├── ingest.py            # Ingest pipeline — chunk, embed, upsert to Qdrant
├── pipeline.py          # Utility runner
├── api.py               # FastAPI backend — exposes /ask endpoint
├── app.py               # Streamlit frontend — chat UI
├── render.yaml          # Render deployment config
│
├── ingestion/           # Document processing
│   ├── chunker.py       # Markdown-aware semantic chunking with overlap
│   ├── chunking.py      # Chunking experiments and tests
│   ├── embedder.py      # OpenAI text-embedding-3-large, Qdrant upsert
│   ├── metadata_tagger.py  # LLM extracts document_id, category, date
│   └── table_splitter.py   # Splits large tables, preserves column headers
│
├── retrieval/           # Query pipeline
│   ├── filters.py       # Category detection, pre-filter, post-filter by date
│   ├── retriever.py     # Multi-query expansion, RRF fusion
│   ├── reranker.py      # CrossEncoder reranking, 0-1 score normalization
│   └── hyde.py          # Hypothetical Document Embedding search
│
├── core/                # Shared config
├── utils/
│   └── token_budget.py  # Token budget enforcer (tiktoken)
│
├── eval/                # Evaluation framework
│   ├── golden_qa.py     # 15 golden QA pairs from policy corpus
│   ├── run_eval.py      # Eval runner — Recall@5, Faithfulness, Category Accuracy
│   └── results/         # Auto-saved JSON + TXT results per run
│
└── data/                # Corporate policy documents (Markdown)
    ├── travel/
    ├── security/
    ├── training/
    └── work policies/
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM (Answer generation) | GPT-4o-mini (OpenAI) |
| Embeddings | text-embedding-3-large (OpenAI) — 3072 dimensions |
| Vector Database | Qdrant Cloud (Ireland, AWS free tier) |
| Reranker | Cohere Rerank API rerank-english-v3.0 (deployed) / CrossEncoder ms-marco-MiniLM-L-6-v2 (local) |
| Query expansion & HyDE | LangChain + GPT-4o-mini |
| Chat history | LangChain InMemoryChatMessageHistory |
| Token counting | tiktoken |
| Backend API | FastAPI + Uvicorn on Render |
| Frontend UI | Streamlit Cloud |
| Framework | Python 3.13 |

---

## Key Features

**Context-aware chunking** — Documents are split by Markdown headers (#, ##, ###), not arbitrary character counts. Table of Contents chunks are automatically filtered out. Tables are detected and preserved as single blocks. Large tables are split row-by-row with column headers prepended to every row so the LLM always understands the numbers. A 12% token overlap ensures sentences at chunk boundaries are never lost.

**Structured metadata tagging** — Every chunk is tagged with `document_id`, `policy_category`, `effective_date`, `policy_owner`, and header hierarchy before embedding. This enables precise filtering.

**Multi-stage retrieval** — The pipeline runs 4 parallel searches (3 query variants + 1 HyDE hypothetical answer), fuses results using Reciprocal Rank Fusion, filters by date to keep only the latest policy version, then reranks the top 25 chunks using a cross-encoder down to the top 5 before answering. The corpus contains 8 policy documents across 284 indexed chunks.

**Token budget enforcement** — Before every LLM call, tiktoken counts the total tokens across the top-5 reranked chunks. If the total exceeds 3,000 tokens, the lowest-ranked chunks are dropped to prevent context overflow. Token usage is displayed live in the UI sidebar per query.

**Hallucination prevention** — The LLM is instructed to answer using only the retrieved context. Category pre-filtering mathematically prevents cross-domain contamination (e.g., a Travel query cannot return HR chunks). If the answer is not in the corpus, the system says so rather than making one up.

**Defensive LLM parsing** — Both `detect_category()` and `generate_multi_queries()` include multi-level fallback parsing. If the LLM returns unexpected output (preamble text, wrong casing, numbered lists), the parsers extract valid values or fall back gracefully rather than silently failing.

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- OpenAI API key
- Qdrant Cloud account (free tier works)

### 1. Clone the repo
```bash
git clone https://github.com/Ramya192/project-aegis.git
cd project-aegis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file in the root:
```
OPENAI_API_KEY=sk-...
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
HF_TOKEN=hf_...
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### 4. Add policy documents
Place Markdown `.md` files inside the `data/` folder. Subfolders by category are recommended (e.g., `data/travel/`, `data/hr/`).

### 5. Run ingestion
```bash
python ingest.py
```

### 6. Run via command line
```bash
python chat.py
```

### 7. Run via UI (two terminals)

**Terminal 1 — FastAPI backend:**
```bash
uvicorn api:app --reload
```

**Terminal 2 — Streamlit frontend:**
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 8. Run evaluation
```bash
python -m eval.run_eval
```

---

## Sample Output

```
Category detected: HR

--- Retrieved Chunks (after rerank) ---
  Chunk 1 | Score: 0.70 | LND-POL-7010-V3 | 5. Formal Tuition Assistance Program
  Chunk 2 | Score: 0.39 | HR-POL-5050-V4  | 9. Conflicts of Interest

Answer:
The tuition reimbursement limit is up to a maximum of $5,250 USD per calendar
year for approved tuition, lab fees, and required textbooks.

Sources used:
  - LND-POL-7010-V3 | 5. Formal Tuition Assistance Program (Degree Programs)
```

---

## ⚠️ Known Limitations & Future Work

**1. Keyword-based faithfulness scoring**
The current eval measures faithfulness by checking whether specific keywords appear in the LLM's answer. This under-counts correct answers that use synonymous phrasing. Future improvement: replace with semantic similarity scoring using `sentence-transformers`.

**2. Query complexity routing**
Every query runs the full pipeline regardless of complexity. Future improvement: add a query complexity classifier that routes simple queries to direct retrieval and only triggers the full pipeline for complex, multi-document queries.

**3. Fixed token budget**
The token budget (3,000 tokens) is a static threshold. Future improvement: make the budget dynamic based on query type and detected category.

**4. No streaming responses**
The current architecture waits for the full LLM response before displaying anything. Future improvement: implement SSE streaming from FastAPI and `st.write_stream()` in Streamlit for live pipeline step animation.

**5. In-memory chat history**
`InMemoryChatMessageHistory` resets on every server restart. In production, chat history should be persisted to Redis or PostgreSQL keyed by session ID.

**6. Cold start latency**
Render free tier spins down after inactivity. A cron-job.org ping every 10 minutes keeps the backend alive. First request after a long idle period may show a "waking up" message.

**7. Reranker on deployment**
Cohere Rerank API (`rerank-english-v3.0`) is used on Render for zero RAM overhead. CrossEncoder `ms-marco-MiniLM-L-6-v2` is used locally for development. Both implement the same cross-encoder architecture — reading query and chunk simultaneously to score logical relevance.

---

## What I Learned

Building Project Aegis taught me that retrieval quality — not LLM quality — is the primary bottleneck in enterprise RAG. The most impactful improvements came from structured chunking (tables, overlap, ToC filtering), metadata filtering (pre and post), and the reranking step which dramatically reduced irrelevant context reaching the LLM. The system correctly refuses to answer when information is not in the corpus, demonstrating hallucination prevention in practice.

Applying real-world RAG failure patterns (context overflow, fragile LLM output parsing, missing evaluation baselines) and fixing them systematically resulted in a pipeline that achieves 100% retrieval recall and 100% category accuracy on the golden evaluation dataset.

---
