---
title: Project Aegis API
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---


# Project Aegis — Advanced Enterprise RAG System

> **IITM Pravartak Advanced PG Certificate in Agentic AI — Agentic AI Assignment**  
> A production-grade, context-aware RAG chatbot built to navigate complex corporate policy documents with high accuracy.

🚀 **Live Demo:** https://project-aegis-policy-intelligence.streamlit.app/  
🔧 **API Backend:** https://ramya192-project-aegis-api.hf.space
👩‍💻 **Built by:** Ramya Priyanka A

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
| **C** — Core approach | An 8-stage retrieval pipeline — MQE + HyDE → RRF fusion → date filter → Reranker (Cohere on deployment / CrossEncoder locally) → token budget → LLM | Solution design |
| **D** — Details | Each technique justified by a specific failure mode it solves — not added for complexity | Implementation |
| **E** — Evaluation | RAGAS RAG Triad (27 samples, 0 errors): Context Precision 0.796, Context Recall 0.778, Faithfulness 0.713, Answer Relevancy 0.892, Answer Correctness 0.725 | Results |
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

Aegis includes a formal RAGAS evaluation framework (`eval/`) built on 31 ground truth Q&A pairs drawn from the actual policy corpus, covering all 5 policy categories (Travel, HR, IT Security, Learning & Development, Performance).

**Run the evaluation:**
```bash
# Step 1: Generate ground truth (run once)
python -m eval.generate_ground_truth

# Step 2: Run RAGAS evaluation
python -m eval.run_ragas_eval
```

See the **📊 RAG Evaluation (RAGAS Framework)** section below for full metric definitions, category breakdown, and latest results.

---

## 📊 RAG Evaluation (RAGAS Framework)

Aegis is evaluated using the **RAG Triad** — the industry-standard methodology for measuring both retrieval quality and generation quality independently. The evaluation framework lives in `eval/` and runs against the actual production pipeline (`chat.py`), not a mock retriever.

### Methodology

**Ground Truth Dataset:** 28 Q&A pairs auto-generated from the 8 policy documents using GPT-4o-mini, plus 3 manually crafted edge-case questions (clawback repayment schedule, mileage rate coverage, clean device protocol) — 31 total covering all 5 policy categories.

**Pipeline under test:** The full 8-stage Aegis pipeline — `detect_category → multi_query_expansion → pre_filter → HyDE → RRF_fusion → post_filter_by_date → CrossEncoder_rerank → LLM` — is executed for every evaluation question. RAGAS receives the LLM's actual answer and the actual retrieved chunks, not synthetic inputs.

**Evaluation model:** RAGAS uses `gpt-4o-mini` as the LLM judge and `text-embedding-3-small` for semantic similarity scoring (Answer Relevancy, Answer Correctness).

---

### Evaluation Results

**Run: `python -m eval.generate_ground_truth && python -m eval.run_ragas_eval`**

#### Overall Scores

| Metric | Score | Threshold | Status |
|---|---|---|---|
| **Context Precision** | **0.796** | ≥ 0.80 | 🟡 Near threshold |
| **Context Recall** | **0.778** | ≥ 0.85 | 🟡 Room to improve |
| **Context Relevancy** | N/A | ≥ 0.75 | Not in installed RAGAS version |
| **Faithfulness** | **0.713** | ≥ 0.85 | 🟡 Acceptable |
| **Answer Relevancy** | **0.892** | ≥ 0.85 | ✅ Exceeds threshold |
| **Answer Correctness** | **0.725** | ≥ 0.70 | ✅ Meets threshold |

> Run: `20260517_211711` · 27 samples · 0 pipeline errors · model: `gpt-4o-mini`
> Full results: `eval/results/ragas_20260517_211711.json`

---

### What Each Metric Measures

#### 🔍 Retrieval Metrics (The Search Phase)
These measure the quality of the vector search, metadata filtering, and CrossEncoder reranker. They answer: *"Did we find the right documents, ranked correctly?"*

**Context Precision** — Measures ranking quality. Checks whether the truly relevant chunks are positioned at the top of the retrieved set. Low precision means the LLM receives irrelevant text before the answer, risking the "Lost in the Middle" failure mode. Aegis addresses this with CrossEncoder reranking (Cohere Rerank on deployment, ms-marco-MiniLM-L-6-v2 locally).

**Context Recall** — Measures coverage. Checks whether all information needed to answer the question was actually retrieved. Low recall means the LLM is missing facts, which is the root cause of hallucination. Aegis addresses this via Multi-Query Expansion (3 variants) + HyDE + RRF fusion across 4 parallel searches.

**Context Relevancy** — Measures signal-to-noise ratio within retrieved chunks. Scores the fraction of sentences in retrieved chunks that are actually relevant to the query vs. filler text. Aegis addresses this via category pre-filtering (`detect_category → WHERE policy_category = X`) which mathematically prevents cross-domain contamination.

#### 🤖 Generation Metrics (The Response Phase)
These measure whether the LLM used the retrieved context correctly. They answer: *"Did the bot answer faithfully without hallucinating?"*

**Faithfulness (Anti-Hallucination)** — Every factual claim in the LLM's answer is verified against the retrieved context. A claim that is true but not traceable to the context is penalised. Aegis enforces context-only answering via the system prompt: *"Answer using ONLY the context below."*

**Answer Relevancy** — Measures whether the response actually addresses what the user asked. A response can be 100% faithful to the context but still fail if it answers the wrong question. Measured by generating reverse questions from the answer and computing semantic similarity to the original query.

**Answer Correctness** — Compares the LLM's answer against the ground truth reference answer using semantic similarity (BERTScore-equivalent). This is the end-to-end quality metric — it captures both factual accuracy and completeness.

---

### Category Breakdown

RAGAS scores are also broken down by policy category to identify domain-specific weaknesses:

| Category | Context Precision | Context Recall | Faithfulness | Answer Correctness |
|---|---|---|---|---|
| Travel | 0.831 | 0.762 | 0.698 | 0.741 |
| HR | 0.771 | 0.789 | 0.724 | 0.712 |
| IT | 0.786 | 0.783 | 0.717 | 0.722 |

> Per-category breakdown from `eval/results/ragas_20260517_211711.json`. Travel scores highest on Context Precision (0.831) due to strong category pre-filtering. HR recall (0.789) is the strongest across categories, reflecting the broad HR policy corpus coverage.

---

### Running the Evaluation

```bash
# Step 1: Generate ground truth Q&A dataset (run once)
python -m eval.generate_ground_truth

# Step 2: Run full RAGAS evaluation against the live pipeline
python -m eval.run_ragas_eval
```

Results are saved automatically to `eval/results/ragas_<timestamp>.json` and `eval/results/ragas_<timestamp>.txt`.

> ⚠️ **API cost estimate:** Running all 31 samples consumes approximately $0.80–$1.20 in OpenAI API credits (pipeline calls + RAGAS judge calls).

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
├── eval/                         # Evaluation framework (RAGAS)
│   ├── generate_ground_truth.py  # GPT-generates 28+ Q&A pairs from policy corpus
│   ├── run_ragas_eval.py         # RAGAS runner — 6 RAG Triad metrics, category breakdown
│   ├── ground_truth.json         # Auto-generated ground truth dataset (31 Q&A pairs)
│   └── results/                  # Auto-saved JSON + TXT results per run
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

**1. RAGAS evaluation requires live API calls**
Running `run_ragas_eval.py` executes the full Aegis pipeline for every ground truth question and uses GPT-4o-mini as an LLM judge for each metric. This costs approximately $0.80–$1.20 per full evaluation run. Future improvement: cache pipeline outputs and run RAGAS scoring separately to reduce cost on repeat evaluations.

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

Applying real-world RAG failure patterns (context overflow, fragile LLM output parsing, 
missing evaluation baselines) and fixing them systematically resulted in a pipeline that 
achieves Answer Relevancy of 0.892 and Context Precision of 0.796 on a RAGAS evaluation 
across 27 ground truth Q&A pairs — with zero pipeline errors across all samples.

---
