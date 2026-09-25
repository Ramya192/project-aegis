# Project Aegis — Advanced Enterprise RAG System

> **Built as part of the IITM Pravartak Advanced PG Certificate in Agentic AI**  
> An end-to-end deployed, context-aware RAG chatbot for navigating complex corporate policy documents — from structure-aware ingestion to evaluated, cited answers.

🚀 **Live Demo:** https://project-aegis-policy-intelligence.streamlit.app/  
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
│  • Falls back to unfiltered if 'X' has no   │
│    chunks (e.g. Legal/Compliance queries)   │
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
Streamlit Community Cloud  (single free service: UI + retrieval pipeline in one process)
        ↓            ↓             ↓
  Qdrant Cloud   OpenAI API   Cohere Rerank API
  (vectors)      (gpt-4o-mini, (rerank-english-v3.0)
                  embeddings)
```

- **App:** Streamlit Community Cloud — auto-deploys on every GitHub push. The UI calls the pipeline in-process (`service.py`); there is no separate API server.
- **Secrets:** `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `COHERE_API_KEY` in Streamlit → App settings → Secrets (template: `.streamlit/secrets.toml.example`)
- **Vector DB:** Qdrant Cloud (free tier)
- **Reranker:** Cohere Rerank API (zero local RAM — no torch in the deployed image)
- **Cost guards:** 10 queries per session (clearing the conversation does not reset it) and 200 queries per day across all visitors

---

## 🎯 Design Philosophy — ABCDEF Framework

| Letter | Meaning | Aegis |
|---|---|---|
| **A** — Acknowledge | Enterprise RAG fails due to bad chunking, no reranking, and version drift — this system was built to solve those specific failures | Problem statement |
| **B** — Background | 8 corporate policy documents, 285 indexed chunks, BFSI compliance use case requiring zero hallucination | Corpus & context |
| **C** — Core approach | An 8-stage retrieval pipeline — MQE + HyDE → RRF fusion → date filter → Reranker (Cohere on deployment / CrossEncoder locally) → token budget → LLM | Solution design |
| **D** — Details | Each technique justified by a specific failure mode it solves — not added for complexity | Implementation |
| **E** — Evaluation | RAGAS RAG Triad (27 samples, 0 errors): Context Precision 0.967, Context Recall 1.000, Faithfulness 0.969, Answer Relevancy 0.886, Answer Correctness 0.820 | Results |
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

→ **Solution:** CrossEncoder reranking (Cohere Rerank API on deployment, ms-marco-MiniLM-L-6-v2 locally) re-scores the fused chunks (up to 25) by query-document relevance, keeping only the top 5 for the LLM.

**Problem 4 — Silent context overflow**

If 5 reranked chunks each contain dense policy tables, the total token count can silently exceed the LLM's effective context budget, causing truncation or degraded answer quality ("Lost in the Middle" effect).

→ **Solution:** A token budget enforcer (tiktoken) counts tokens before the LLM call and trims from the lowest-ranked chunk upward if the total exceeds 3,000 tokens. Token usage is surfaced in the Streamlit sidebar per query.

Each technique was introduced to solve a specific, observed failure mode — not for complexity's sake.

---

## 📊 Evaluation Results

Aegis includes a formal RAGAS evaluation framework (`eval/`) built on 27 ground truth Q&A pairs drawn from the actual policy corpus, covering the Travel, HR (including Learning & Development and Performance) and IT Security policy categories.

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

Aegis is evaluated using the **RAG Triad** — the industry-standard methodology for measuring both retrieval quality and generation quality independently. The evaluation framework lives in `eval/` and runs against the same pipeline the deployed app uses (`chat.py`), not a mock retriever.

### Methodology

**Ground Truth Dataset:** 27 Q&A pairs drawn from the 8 policy documents (`eval/ground_truth.json`), spanning the Travel, HR and IT Security categories.

**Pipeline under test:** The full 8-stage Aegis pipeline — `detect_category → multi_query_expansion → pre_filter → HyDE → RRF_fusion → post_filter_by_date → CrossEncoder_rerank → LLM` — is executed for every evaluation question. RAGAS receives the LLM's actual answer and the actual retrieved chunks, not synthetic inputs.

**Scope and caveats:** This is a 27-question regression benchmark for the Aegis pipeline, not a general accuracy claim. The questions are derived from the same 8 policy documents that are indexed, and RAGAS scores come from an LLM judge, so they vary somewhat between runs. Scores are best read as relative measures for comparing pipeline changes.

**Evaluation model:** RAGAS uses `gpt-4o-mini` as the LLM judge and `text-embedding-3-small` for semantic similarity scoring (Answer Relevancy, Answer Correctness).

---

### Evaluation Results

**Run: `python -m eval.generate_ground_truth && python -m eval.run_ragas_eval`**

#### Overall Scores

| Metric | Score | Threshold | Status |
|---|---|---|---|
| **Context Precision** | **0.967** | ≥ 0.80 | ✅ Exceeds threshold |
| **Context Recall** | **1.000** | ≥ 0.85 | ✅ Exceeds threshold |
| **Noise Sensitivity** (lower is better) | **0.412** | — | 🟡 Some irrelevant context still reaches the LLM |
| **Faithfulness** | **0.969** | ≥ 0.85 | ✅ Exceeds threshold |
| **Answer Relevancy** | **0.886** | ≥ 0.85 | ✅ Exceeds threshold |
| **Answer Correctness** | **0.820** | ≥ 0.70 | ✅ Exceeds threshold |

> Run: `20260925_100212` · 27 samples · 0 pipeline errors · model: `gpt-4o-mini` · reranker: Cohere `rerank-english-v3.0`
> Full results: `eval/results/ragas_20260925_100212.json`

These scores come from a 27-question regression benchmark over this corpus, not a general accuracy claim.

**Change vs. the previous run (`20260925_091755`, same 27 questions):** Context Precision 0.893 → 0.967, Context Recall 0.889 → 1.000, Faithfulness 0.818 → 0.969, Answer Correctness 0.798 → 0.820, Answer Relevancy 0.915 → 0.886, Noise Sensitivity 0.323 → 0.412 (worse). Most of the change comes from how the evaluation is measured, not from the pipeline: earlier runs gave RAGAS only a 300-character preview of each retrieved chunk, while the LLM answered from the full chunk, so faithfulness and recall were understated. RAGAS now sees the full chunks the LLM saw. The same change likely explains the higher noise sensitivity, since longer contexts give the judge more unrelated text to find. The pipeline changes in the same run: the query category is detected once per question, the prompt tells the LLM to say when the answer isn't in the documents, Cohere receives untruncated chunks, and the prose next to large tables is now indexed. RAGAS judge scores also vary somewhat from run to run.

---

### What Each Metric Measures

#### 🔍 Retrieval Metrics (The Search Phase)
These measure the quality of the vector search, metadata filtering, and CrossEncoder reranker. They answer: *"Did we find the right documents, ranked correctly?"*

**Context Precision** — Measures ranking quality. Checks whether the truly relevant chunks are positioned at the top of the retrieved set. Low precision means the LLM receives irrelevant text before the answer, risking the "Lost in the Middle" failure mode. Aegis addresses this with CrossEncoder reranking (Cohere Rerank on deployment, ms-marco-MiniLM-L-6-v2 locally).

**Context Recall** — Measures coverage. Checks whether all information needed to answer the question was actually retrieved. Low recall means the LLM is missing facts, which is the root cause of hallucination. Aegis addresses this via Multi-Query Expansion (3 variants) + HyDE + RRF fusion across 4 parallel searches.

**Noise Sensitivity** — Measures how often the answer contains errors caused by irrelevant retrieved context (lower is better). Aegis reduces noise via category pre-filtering (`detect_category → WHERE policy_category = X`), which keeps most cross-domain chunks out of the candidate set.

#### 🤖 Generation Metrics (The Response Phase)
These measure whether the LLM used the retrieved context correctly. They answer: *"Did the bot answer faithfully without hallucinating?"*

**Faithfulness (Anti-Hallucination)** — Every factual claim in the LLM's answer is verified against the retrieved context. A claim that is true but not traceable to the context is penalised. Aegis enforces context-only answering via the system prompt: *"Answer using ONLY the context below."*

**Answer Relevancy** — Measures whether the response actually addresses what the user asked. A response can be 100% faithful to the context but still fail if it answers the wrong question. Measured by generating reverse questions from the answer and computing semantic similarity to the original query.

**Answer Correctness** — Compares the LLM's answer against the ground truth reference answer using semantic similarity (BERTScore-equivalent). This is the end-to-end quality metric — it captures both factual accuracy and completeness.

---

### Running the Evaluation

```bash
# Step 1: Generate ground truth Q&A dataset (run once)
python -m eval.generate_ground_truth

# Step 2: Run full RAGAS evaluation against the live pipeline
python -m eval.run_ragas_eval
```

Results are saved automatically to `eval/results/ragas_<timestamp>.json` and `eval/results/ragas_<timestamp>.txt`.

> ⚠️ **Note:** The evaluation makes live API calls — the full pipeline (OpenAI + Qdrant + Cohere rerank) for each of the 27 questions, plus GPT-4o-mini judge calls for every RAGAS metric. It needs valid API keys and uses paid OpenAI credits; a Cohere trial key allows about 1,000 rerank calls per month.

---

## Folder Structure

```
project-aegis/
│
├── chat.py              # Pipeline entry point — ask questions, get answers
├── ingest.py            # Ingest pipeline — chunk, embed, upsert to Qdrant
├── service.py           # In-process query pipeline used by the UI
├── app.py               # Streamlit app — chat UI
├── requirements.txt     # Runtime deps (what Streamlit Cloud installs)
├── requirements-dev.txt # Local CrossEncoder + RAGAS eval
│
├── ingestion/           # Document processing
│   ├── chunker.py       # Markdown-aware semantic chunking with overlap
│   ├── embedder.py      # OpenAI text-embedding-3-large, Qdrant upsert
│   ├── metadata_tagger.py  # LLM extracts document_id, category, date
│   └── table_splitter.py   # Splits large tables, preserves column headers
│
├── retrieval/           # Query pipeline
│   ├── filters.py       # Category detection, pre-filter, post-filter by date
│   ├── retriever.py     # Multi-query expansion, RRF fusion
│   ├── reranker.py      # Cohere Rerank (deployed) / CrossEncoder (local) reranking
│   └── hyde.py          # Hypothetical Document Embedding search
│
├── utils/
│   └── token_budget.py  # Token budget enforcer (tiktoken)
│
├── eval/                         # Evaluation framework (RAGAS)
│   ├── generate_ground_truth.py  # GPT-generates Q&A pairs from the policy corpus
│   ├── run_ragas_eval.py         # RAGAS runner — 6 RAG Triad metrics
│   ├── ground_truth.json         # Auto-generated ground truth dataset (27 Q&A pairs)
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
| Vector Database | Qdrant Cloud (AWS us-east-1, free tier) |
| Reranker | Cohere Rerank API rerank-english-v3.0 (deployed) / CrossEncoder ms-marco-MiniLM-L-6-v2 (local) |
| Query expansion & HyDE | LangChain + GPT-4o-mini |
| Chat history | LangChain InMemoryChatMessageHistory |
| Token counting | tiktoken |
| App hosting | Streamlit Community Cloud (UI + pipeline in one process) |
| Framework | Python 3.13 |

---

## Key Features

**Context-aware chunking** — Documents are split by Markdown headers (#, ##, ###), not arbitrary character counts. Table of Contents chunks are automatically filtered out. Tables are detected and preserved as single blocks. Large tables are split row-by-row with column headers prepended to every row so the LLM always understands the numbers. A 12% token overlap ensures sentences at chunk boundaries are never lost.

**Structured metadata tagging** — Every chunk is tagged with `document_id`, `policy_category`, `effective_date`, `policy_owner`, and header hierarchy before embedding. This enables precise filtering.

**Multi-stage retrieval** — The pipeline runs up to 5 searches (the original query, 3 LLM-generated variants, and 1 HyDE hypothetical answer), fuses results using Reciprocal Rank Fusion, filters by date to keep only the latest policy version, then reranks the top 25 chunks using a cross-encoder down to the top 5 before answering. The corpus contains 8 policy documents across 285 indexed chunks.

**Token budget enforcement** — Before every LLM call, tiktoken counts the total tokens across the top-5 reranked chunks. If the total exceeds 3,000 tokens, the lowest-ranked chunks are dropped to prevent context overflow. Token usage is displayed live in the UI sidebar per query.

**Hallucination prevention** — The LLM is instructed to answer using only the retrieved context. Category pre-filtering keeps cross-domain chunks out of the candidate set (e.g., a Travel query does not surface HR chunks); if the detected category has no chunks in the corpus, retrieval falls back to an unfiltered search rather than returning nothing. If the answer is not in the corpus, the system says so rather than making one up.

**Defensive LLM parsing** — Both `detect_category()` and `generate_multi_queries()` include multi-level fallback parsing. If the LLM returns unexpected output (preamble text, wrong casing, numbered lists), the parsers extract valid values or fall back gracefully rather than silently failing.

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- OpenAI API key
- Qdrant Cloud account (free tier works)
- Cohere API key (free trial key works; optional locally)

### 1. Clone the repo
```bash
git clone https://github.com/Ramya192/project-aegis.git
cd project-aegis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt        # runtime (what Streamlit Cloud installs)
pip install -r requirements-dev.txt    # optional: local CrossEncoder + RAGAS eval
```

### 3. Configure environment
Create a `.env` file in the root:
```
OPENAI_API_KEY=sk-...
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
COHERE_API_KEY=your-cohere-api-key   # optional locally; falls back to CrossEncoder
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

### 7. Run via UI
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 8. Run evaluation
```bash
python -m eval.run_ragas_eval   # needs requirements-dev.txt
```

---

## Sample Output

```
Category detected: HR

Answer:
The tuition reimbursement limit is up to a maximum of $5,250 USD per calendar
year for approved tuition, lab fees, and required textbooks.

Sources used:
  - LND-POL-7010-V3 | 5. Formal Tuition Assistance Program (Degree Programs)
```

---

## ⚠️ Known Limitations & Future Work

**1. RAGAS evaluation requires live API calls**
Running `run_ragas_eval.py` executes the full Aegis pipeline for every ground truth question and uses GPT-4o-mini as an LLM judge for each metric. This uses paid API credits on every run. Future improvement: cache pipeline outputs and run RAGAS scoring separately to reduce cost on repeat evaluations.

**2. Query complexity routing**
Every query runs the full pipeline regardless of complexity. Future improvement: add a query complexity classifier that routes simple queries to direct retrieval and only triggers the full pipeline for complex, multi-document queries.

**3. Fixed token budget**
The token budget (3,000 tokens) is a static threshold. Future improvement: make the budget dynamic based on query type and detected category.

**4. No streaming responses**
The current architecture waits for the full LLM response before displaying anything. Future improvement: stream the LLM response with `st.write_stream()` in Streamlit for live pipeline step animation.

**5. In-memory chat history**
`InMemoryChatMessageHistory` resets on every server restart. The store is bounded (200 most recent sessions, last 5 turns sent to the LLM), but a persistent store such as Redis or PostgreSQL keyed by session ID would survive restarts.

**6. Cold start latency**
Streamlit Community Cloud puts idle apps to sleep; the first visit after a long idle period shows a "wake up" screen and the first query re-imports the pipeline. Qdrant Cloud free clusters are also suspended after ~1 week of inactivity, so visit the app (or the Qdrant dashboard) periodically.

**7. Category classifier vs. corpus tags**
The category classifier can return categories (e.g. Legal, Compliance) that no chunk is tagged with, because the corpus only contains Travel, HR and IT. In that case retrieval falls back to an unfiltered search. Future improvement: derive the classifier's allowed categories from the tags actually present in the index.

**8. Reranker on deployment**
Cohere Rerank API (`rerank-english-v3.0`) is used on Streamlit Cloud for zero RAM overhead. CrossEncoder `ms-marco-MiniLM-L-6-v2` is used locally for development. Both implement the same cross-encoder architecture — reading query and chunk simultaneously to score logical relevance. If the Cohere call fails (rate limit, outage), the pipeline falls back to the local CrossEncoder when installed, otherwise to the RRF order, so the user still gets an answer.

---

## What I Learned

Building Project Aegis taught me that retrieval quality — not LLM quality — is the primary bottleneck in enterprise RAG. The most impactful improvements came from structured chunking (tables, overlap, ToC filtering), metadata filtering (pre and post), and the reranking step which dramatically reduced irrelevant context reaching the LLM. The system correctly refuses to answer when information is not in the corpus, demonstrating hallucination prevention in practice.

Applying real-world RAG failure patterns (context overflow, fragile LLM output parsing, 
missing evaluation baselines) and fixing them systematically resulted in a pipeline that 
achieves Faithfulness of 0.969 and Context Precision of 0.967 on a RAGAS evaluation 
across 27 ground truth Q&A pairs — with zero pipeline errors across all samples.

---
