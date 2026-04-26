# Project Aegis — Advanced Enterprise RAG System

> **IITM Pravartak Advanced PG Certificate in Agentic AI — Project A**  
> A production-grade, context-aware RAG chatbot built to navigate complex corporate policy documents with high accuracy.

---

## Objective

Most RAG systems fail in enterprise settings because they split documents arbitrarily, lose table structure, and retrieve irrelevant context. Project Aegis solves this by building a multi-stage pipeline that understands document structure, filters by intent, and reranks results before generating an answer.

**The system can answer questions like:**
- *"What is the taxi reimbursement limit?"* → $50 per trip (TRV-POL-2005-V3)
- *"What is the maternity leave policy?"* → 16 weeks at 100% pay (HR-POL-4001-V6)
- *"What is the tuition reimbursement limit?"* → $5,250 USD per year (LND-POL-7010-V3)

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
│  • Scores each chunk against query (0–1)    │
│  • Prunes to Top 5 most relevant chunks     │
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

## Folder Structure

```
project-aegis/
│
├── chat.py              # Main entry point — ask questions, get answers
├── ingest.py            # Ingest pipeline — chunk, embed, upsert to Qdrant
├── pipeline.py          # Utility runner
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
├── utils/               # Dev utilities
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
| Embeddings | text-embedding-3-large (OpenAI) |
| Vector Database | Qdrant Cloud |
| Reranker | CrossEncoder ms-marco-MiniLM-L-6-v2 |
| Query expansion & HyDE | LangChain + GPT-4o-mini |
| Chat history | LangChain InMemoryChatMessageHistory |
| Framework | Python 3.13 |

---

## Key Features

**Context-aware chunking** — Documents are split by Markdown headers (#, ##, ###), not arbitrary character counts. Tables are detected and preserved as single blocks. Large tables are split row-by-row with column headers prepended to every row so the LLM always understands the numbers. A 12% token overlap ensures sentences at chunk boundaries are never lost.

**Structured metadata tagging** — Every chunk is tagged with `document_id`, `policy_category`, `effective_date`, `policy_owner`, and header hierarchy before embedding. This enables precise filtering.

**Multi-stage retrieval** — The pipeline runs 4 parallel searches (3 query variants + 1 HyDE hypothetical answer), fuses results using Reciprocal Rank Fusion, filters by date to keep only the latest policy version, then reranks the top 25 chunks using a cross-encoder down to the top 5 before answering.

**Hallucination prevention** — The LLM is instructed to answer using only the retrieved context. Category pre-filtering mathematically prevents cross-domain contamination (e.g., a Travel query cannot return HR chunks).

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
This chunks, tags, embeds, and upserts all documents to Qdrant.

### 6. Ask questions
```bash
python chat.py
```

---

## Sample Output

```
Category detected: Travel

--- Retrieved Chunks (after rerank) ---
  Chunk 1 | Score: 0.55 | TRV-POL-1001-V4 | 6. Ground Transportation
  Chunk 2 | Score: 0.52 | TRV-POL-3012-V2 | 9. Tolls, Parking, and Ancillary Transit Costs
  Chunk 3 | Score: 0.68 | TRV-POL-2005-V3 | Ground Transportation

Answer:
The taxi reimbursement limit is up to $50 per trip.

Sources used:
  - TRV-POL-2005-V3 | Ground Transportation
  - TRV-POL-1001-V4 | 6. Ground Transportation and Vehicle Policies
```

---

## What I Learned

Building Project Aegis taught me that retrieval quality — not LLM quality — is the primary bottleneck in enterprise RAG. The most impactful improvements came from structured chunking (tables, overlap), metadata filtering (pre and post), and the reranking step which dramatically reduced irrelevant context reaching the LLM.

---

*Built as part of the IITM Pravartak Advanced PG Certificate in Agentic AI (December 2025 – June 2026)*
