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
│  • LLM detects 1-2 categories (Travel/HR/IT)│
│  • WHERE policy_category IN (X, Y) in Qdrant│
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
│  • Keeps the 8 most relevant chunks         │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│     Token Budget Enforcer (tiktoken)        │
│  • Counts tokens across the 8 chunks        │
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
- **Cost guards:** 10 queries per visit (clearing the conversation does not reset it; the sidebar says so) and 200 queries per day across all visitors
- **Source cards:** the model ends each answer with a `SOURCES:` line naming the passages it relied on; those are shown as cards with a cleaned preview and, when the chunk is longer, an expander with the full text. The other passages it received are listed under "(not cited)". If the answer is "could not find it" and nothing was cited, no card is shown and the closest passages are listed as "none relevant".
- **Answers:** `temperature=0` so the same question gives the same answer (it was 1.0 before, which reversed a rule once and half-refused a question once)

---

## 🎯 Design Philosophy — ABCDEF Framework

| Letter | Meaning | Aegis |
|---|---|---|
| **A** — Acknowledge | Enterprise RAG fails due to bad chunking, no reranking, and version drift — this system was built to solve those specific failures | Problem statement |
| **B** — Background | 8 corporate policy documents, 286 indexed chunks, BFSI compliance use case requiring zero hallucination | Corpus & context |
| **C** — Core approach | An 8-stage retrieval pipeline — MQE + HyDE → RRF fusion → date filter → Reranker (Cohere on deployment / CrossEncoder locally) → token budget → LLM | Solution design |
| **D** — Details | Each technique justified by a specific failure mode it solves — not added for complexity | Implementation |
| **E** — Evaluation | RAGAS RAG Triad (27 samples, 0 errors): Context Precision 0.966, Context Recall 1.000, Faithfulness 1.000, Answer Relevancy 0.877, Answer Correctness 0.776 | Results |
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

→ **Solution:** CrossEncoder reranking (Cohere Rerank API on deployment, ms-marco-MiniLM-L-6-v2 locally) re-scores the fused chunks (up to 25) by query-document relevance, keeping the top 8 for the LLM. There is deliberately no minimum-score cutoff, because Cohere scores answers that need reasoning, or that cover only part of a question, very low.

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
| **Context Precision** | **0.966** | ≥ 0.80 | ✅ Exceeds threshold |
| **Context Recall** | **1.000** | ≥ 0.85 | ✅ Exceeds threshold |
| **Noise Sensitivity** (lower is better) | **0.440** | — | 🟡 Some irrelevant context still reaches the LLM |
| **Faithfulness** | **1.000** | ≥ 0.85 | ✅ Exceeds threshold |
| **Answer Relevancy** | **0.877** | ≥ 0.85 | ✅ Exceeds threshold |
| **Answer Correctness** | **0.776** | ≥ 0.70 | ✅ Exceeds threshold |

> Run: `20260926_114126` · 27 samples · 0 pipeline errors · model: `gpt-4o-mini` at temperature 0 · reranker: Cohere `rerank-english-v3.0`
> 1 of the 162 metric values (1 Faithfulness) was not returned by the judge and is left out, so Faithfulness averages 26 questions.
> Full results, including per-question scores: `eval/results/ragas_20260926_114126.json`

These scores come from a 27-question regression benchmark over this corpus, not a general accuracy claim. The questions are single-fact lookups written from the same 8 documents, which is why Context Recall is 1.000 (no question scored below 1.0). That shows this set is easy, so the harder set below is the better guide to the system's weaknesses.

**Run-to-run variation.** The five most recent runs on these 27 questions (`20260925_100212`, `_105722`, `_171119`, `_182155`, `20260926_114126`) gave Context Precision 0.966–0.992, Faithfulness 0.969–1.000, Answer Relevancy 0.877–0.917, Answer Correctness 0.773–0.820 and Noise Sensitivity 0.365–0.440, with Context Recall 1.000 in all five. The pipeline changed between them, and RAGAS judge scores also move from run to run, so differences of a few hundredths are noise. The last two runs followed the retrieval change described below (its lower Context Precision is the expected cost of sending more chunks to the LLM); the latest also follows the change to temperature 0, the `SOURCES:` citation line and the answer-prompt rules on dates and ineligibility, and its Noise Sensitivity (0.440) is the highest of the five.

**Earlier run (`20260925_091755`).** That run gave RAGAS only a 300-character preview of each retrieved chunk, while the LLM answered from the full chunk, so its faithfulness and recall (0.818 and 0.889) were understated. Later runs pass RAGAS the full chunks the LLM saw.

#### Harder benchmark: cross-document, paraphrased and unanswerable questions

`eval/ground_truth_hard.json` holds 12 questions written to be harder than the main set: 5 need facts from two documents, 4 are worded differently from the documents, and 3 have no answer in the corpus. Run it with `python -m eval.run_hard_eval`. The first run of this set exposed three weaknesses, which were then addressed (see below). Before and after, on the 9 answerable questions:

| Metric | Before (`hard_20260925_170434`) | After (`hard_20260925_181240`) | Latest (`hard_20260926_114416`) |
|---|---|---|---|
| Context Precision | 0.920 | 0.866 | 0.861 |
| Context Recall | 0.833 | 0.926 | 0.907 |
| Faithfulness | 0.852 | 0.950 | 0.913 |
| Answer Relevancy | 0.616 | 0.742 | 0.767 |
| Answer Correctness | 0.637 | 0.733 | 0.728 |
| Noise Sensitivity (lower is better) | 0.143 | 0.185 | 0.273 |

*Before* means one category filter, 5 chunks sent to the LLM and a 0.01 relevance cutoff. *After* means up to two categories, 8 chunks and no cutoff. *Latest* is the same retrieval as *After* plus temperature 0, the `SOURCES:` citation line and the answer-prompt rules (state dates as written, say "not eligible" when a condition fails, cover every part of the question). The 3 unanswerable questions have no reference answer for RAGAS to compare against, so each is scored pass/fail on whether the assistant says the information is not in the documents instead of inventing a figure: 3 / 3 passed in all three runs. That says nothing about over-refusing, which the paraphrase questions test.

Reading the answers: before, 5 of 9 were fully correct, 3 missed a detail and 1 was wrong; after and in the latest run, 7 are fully correct and 2 miss one detail (the 7-day PTO notice; the deduction of owed tuition from the PTO payout), and none is wrong. Between *After* and *Latest*, Faithfulness fell from 0.950 to 0.913 and Noise Sensitivity rose from 0.185 to 0.273 while the answers read the same; with 9 questions I have not tested whether that is judge noise or a real effect. Nine questions is a small sample, so treat this as a diagnostic, not a benchmark score.

**What the first run showed, and what was done:**

- **Cross-category questions (Chicago hotel rate).** The category was detected once and applied as a hard filter to every search, so an L&D-stipend question classified as HR could never retrieve the Travel policy. The classifier can now return up to two categories and the filter accepts either (`policy_category IN (X, Y)`).
- **Questions spanning two topics (PIP and tuition).** Only 5 chunks reached the LLM and the tuition-eligibility chunk ranked 6th, so the assistant reasoned from partial context and wrongly said tuition had no restriction. It now receives 8 chunks.
- **Relevance cutoffs.** Cohere scores a chunk that answers only part of a question, or answers indirectly, very low: 0.041 for the table row "6 to 9 Years" asked as "seven years", and 0.005 for the tuition chunk in the PIP question. A cutoff of 0.1 dropped the first (a false "I could not find it") and a cutoff of 0.01 dropped the second, which also cancelled the benefit of sending 8 chunks. The reranker now has no cutoff. The UI shows the passages the model cited as source cards and lists the rest, which the model still receives, under "(not cited)", so a passage with a low Cohere score is no longer hidden.

**Held-out check.** To avoid grading the fix on the questions that motivated it, four new questions (`eval/ground_truth_heldout.json`: three that need two policy areas and one two-topic question within HR) were written before any change and run on the old pipeline for a retrieval baseline. Right after the change: Context Recall 0.875, Faithfulness 0.938, Answer Correctness 0.848 and Context Precision 0.379. In the latest run (`heldout_20260926_114615`): Context Recall 1.000, Faithfulness 0.950, Answer Correctness 0.824 and Context Precision 0.462 (4 questions, so indicative only). Right after the change three answers were fully correct; on the fourth (return of a laptop when leaving the company) the assistant found the PTO rule but said it could not find the hardware-return rule, which matches an intermittent classifier miss seen for this question in the retrieval ablation below, where one run picked "Other" as its second category instead of IT and the hardware-return chunk was left out. In the latest run all four answers are fully correct, including the laptop question. One passing run does not show the classifier miss is gone, because it is intermittent. The low Context Precision is the price of sending 8 chunks when a question needs facts from two places: only a few of the 8 are relevant.

**Retrieval ablation.** Answer scores are noisy, so retrieval was also measured directly: for each of the 13 answerable questions in both sets, the chunk holding each required fact ("needle") is looked for among the chunks sent to the LLM (22 needed facts, 2 repeats each, `python -m eval.run_retrieval_ablation`; results in `eval/results/ablation_*.json`).

| Setting | Needed facts reaching the LLM | Questions with every fact | Held-out only |
|---|---|---|---|
| Before: 1 category, 5 chunks, 0.01 cutoff | 73% | 54% | 62% |
| Up to 2 categories, 5 chunks, 0.01 cutoff | 84% | 73% | 81% |
| 1 category, 8 chunks, 0.01 cutoff | 73% | 54% | 62% |
| Up to 2 categories, 8 chunks, 0.01 cutoff | 86% | 77% | 88% |
| **After: up to 2 categories, 8 chunks, no cutoff** (two runs) | **91–95%** | **85–92%** | **94–100%** |

The category change is the main gain. Sending 8 chunks did nothing on its own, because the cutoff removed the low-scoring chunk it was meant to admit; the two only worked together once the cutoff was removed. The same settings scored 95% in one run and 91% in another, so differences of a few points between rows are within run-to-run variation (the classifier's choice of a second category is not deterministic).

---

### What Each Metric Measures

#### 🔍 Retrieval Metrics (The Search Phase)
These measure the quality of the vector search, metadata filtering, and CrossEncoder reranker. They answer: *"Did we find the right documents, ranked correctly?"*

**Context Precision** — Measures ranking quality. Checks whether the truly relevant chunks are positioned at the top of the retrieved set. Low precision means the LLM receives irrelevant text before the answer, risking the "Lost in the Middle" failure mode. Aegis addresses this with CrossEncoder reranking (Cohere Rerank on deployment, ms-marco-MiniLM-L-6-v2 locally).

**Context Recall** — Measures coverage. Checks whether all information needed to answer the question was actually retrieved. Low recall means the LLM is missing facts, which is the root cause of hallucination. Aegis addresses this via Multi-Query Expansion (3 variants) + HyDE + RRF fusion across 4 parallel searches.

**Noise Sensitivity** — Measures how often the answer contains errors caused by irrelevant retrieved context (lower is better). Aegis reduces noise via category pre-filtering (`detect_category → WHERE policy_category IN (X, Y)`), which keeps most cross-domain chunks out of the candidate set.

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

```bash
# Optional: the harder set (cross-document, paraphrased, unanswerable questions)
python -m eval.run_hard_eval
python -m eval.run_hard_eval eval/ground_truth_heldout.json heldout   # the held-out questions

# Optional: retrieval-only comparison of pipeline settings
AEGIS_MAX_CATEGORIES=1 AEGIS_CONTEXT_CHUNKS=5 python -m eval.run_retrieval_ablation old_settings
python -m eval.run_retrieval_ablation new_settings
```

Results are saved automatically to `eval/results/ragas_<timestamp>.json` and `.txt` (harder set: `hard_<timestamp>.*`), including per-question scores.

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
│   ├── ground_truth_hard.json    # Harder set: cross-document, paraphrased, unanswerable (12)
│   ├── ground_truth_heldout.json # 4 held-out questions, not used to tune anything
│   ├── run_hard_eval.py          # Runs the harder set (RAGAS + pass/fail for unanswerable)
│   ├── run_retrieval_ablation.py # Did each needed fact reach the LLM? (compares settings)
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

**Multi-stage retrieval** — The pipeline runs up to 5 searches (the original query, 3 LLM-generated variants, and 1 HyDE hypothetical answer), fuses results using Reciprocal Rank Fusion, filters by date to keep only the latest policy version, then reranks the top 25 chunks using a cross-encoder down to the top 8 before answering. The classifier can choose up to two categories, so a question spanning two policy areas searches both. There is deliberately no minimum relevance cutoff on the reranker: cutoffs of 0.1 and 0.01 both dropped chunks the answer needed. The UI shows the passages the model cited as source cards and the rest under "(not cited)". The corpus contains 8 policy documents across 286 indexed chunks.

**Token budget enforcement** — Before every LLM call, tiktoken counts the total tokens across the reranked chunks (8 by default). If the total exceeds 3,000 tokens, the lowest-ranked chunks are dropped to prevent context overflow. Token usage is displayed live in the UI sidebar per query.

**Hallucination prevention** — The LLM is instructed to answer using only the retrieved context. Category pre-filtering keeps cross-domain chunks out of the candidate set (e.g., a Travel query does not surface HR chunks); if the detected category has no chunks in the corpus, retrieval falls back to an unfiltered search rather than returning nothing. If the answer is not in the corpus, the system says so rather than making one up, and the UI then shows no source card. The prompt also tells the model to quote policy dates as written (for example "as of November 15th"), to say plainly "not eligible" when the user's situation fails a required condition, and to mention local or state law caveats when the context contains them.

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
The category classifier can return categories (e.g. Legal, Compliance) that no chunk is tagged with, because the corpus only contains Travel, HR and IT. In that case retrieval falls back to an unfiltered search. The category badge in the UI now shows only the detected categories that returned passages, so a classifier answer such as "Finance" (no document is tagged with it) is no longer displayed. Future improvement: derive the classifier's allowed categories from the tags actually present in the index.

**8. At most two categories per question**
The classifier now returns up to two categories, which fixed the questions that need two policy areas (for example an L&D stipend plus a travel hotel limit). A question spanning three areas still cannot retrieve them all, and the choice of a second category is not deterministic: on one retrieval-ablation run the classifier picked "Other" instead of IT as the second category for the laptop-return question and the rule was missed. Future improvement: use the category as a boost rather than a filter, or search filtered and unfiltered and merge.

**9. Multi-part answers can still drop a detail**
Up to 8 chunks reach the LLM, which fixed the case where a two-topic question lost half its answer, but a detail is occasionally still left out (the 7-day PTO notice; the deduction of owed tuition from the PTO payout). Future improvement: retrieve per sub-question, or check that the answer covers every part of the question.

**10. Sending more chunks lowers Context Precision**
With no relevance cutoff and 8 chunks, more low-relevance text reaches the LLM (Context Precision 0.992 → 0.968 on the main set, 0.920 → 0.866 on the harder set). Faithfulness did not suffer, but token use per question is higher, still well inside the 3,000-token budget.

**11. Reranker on deployment**
Cohere Rerank API (`rerank-english-v3.0`) is used on Streamlit Cloud for zero RAM overhead. CrossEncoder `ms-marco-MiniLM-L-6-v2` is used locally for development. Both implement the same cross-encoder architecture — reading query and chunk simultaneously to score logical relevance. If the Cohere call fails (rate limit, outage), the pipeline falls back to the local CrossEncoder when installed, otherwise to the RRF order, so the user still gets an answer.

---

## What I Learned

Building Project Aegis taught me that retrieval quality — not LLM quality — is the primary bottleneck in enterprise RAG. The most impactful improvements came from structured chunking (tables, overlap, ToC filtering), metadata filtering (pre and post), and the reranking step which dramatically reduced irrelevant context reaching the LLM. The system correctly refuses to answer when information is not in the corpus, demonstrating hallucination prevention in practice.

Applying real-world RAG failure patterns (context overflow, fragile LLM output parsing, 
missing evaluation baselines) and fixing them systematically resulted in a pipeline that 
achieves Faithfulness of 1.000 and Context Precision of 0.966 on a RAGAS evaluation 
across 27 ground truth Q&A pairs — with zero pipeline errors across all samples.

---
