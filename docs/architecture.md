# LearnLens architecture

LearnLens is a study assistant. Students upload course PDFs; the API retrieves relevant passages and asks an open-weight Gemma model (via local Ollama) to answer only from that evidence.

## Overview

```text
Student browser
        |
        v
Next.js frontend
TypeScript, Tailwind CSS
        |
        v
FastAPI backend
        |
        +-- Document ingestion (upload → extract → chunk → embed)
        +-- Semantic retrieval (pgvector)
        +-- Context builder + grounded Q&A (Gemma via Ollama)
        |
        v
PostgreSQL + pgvector
```

## Implemented RAG pipeline

```text
PDF
 ↓
Extract
 ↓
Chunk
 ↓
BGE Embeddings  (BAAI/bge-small-en-v1.5, 384-d)
 ↓
PostgreSQL + pgvector
 ↓
Question
 ↓
Question Embedding
 ↓
Semantic Retrieval
 ↓
Context Builder
 ↓
Gemma (Ollama)
 ↓
Grounded Answer
```

| Stage | Status |
| --- | --- |
| PDF upload / extract / chunk / embed | Implemented |
| PostgreSQL + pgvector persistence | Implemented |
| Semantic retrieval `POST /api/v1/retrieval/search` | Implemented |
| Grounded Q&A `POST /api/v1/qa/ask` | Implemented (Phase 2.7) |
| Source citation UI | Planned (Phase 2.8) |
| Quizzes / summaries / insights / auth | Planned later |

## Components

### Frontend

Next.js app in `frontend/`. Upload and Notion-inspired document workspace exist; Ask wiring to `/qa/ask` is deferred until the backend QA path is verified.

### Backend

| Path | Role |
| --- | --- |
| `main.py` | Application entrypoint |
| `api/` | HTTP routes (health, ready, llm/ready, documents, retrieval, qa) |
| `services/` | Extraction, chunking, embeddings, repository, retrieval, context builder, LLM, QA |
| `models/` | Request/response models |
| `db/` | SQLAlchemy models, settings, session helpers |

### Models

- **Embeddings:** `EMBEDDING_MODEL` (default `BAAI/bge-small-en-v1.5`)
- **Generation:** Gemma via Ollama (`LLM_MODEL`, default `gemma3:4b`)

See [qa.md](qa.md) for Ollama setup and [retrieval.md](retrieval.md) for search details.

## Grounding behavior

1. Embed the question with the same embedding model used for chunks.
2. Retrieve top-k chunks above `RETRIEVAL_MIN_SIMILARITY`.
3. If `retrieval_status` is `insufficient_evidence`, **do not call Gemma**; return a fixed insufficient-evidence answer.
4. Otherwise build delimited context from retrieved chunks only and call Gemma.
5. Retrieved document text is treated as untrusted content (prompt-injection safe delimiters).

## Deployment

Frontend and API are planned for Render with managed PostgreSQL + pgvector. Local development uses Docker Compose for PostgreSQL and a local Ollama process for Gemma.

## Repository layout

```text
LearnLens/
├── frontend/          Next.js client
├── backend/           FastAPI application
├── docs/              Architecture and stage notes
├── README.md
├── .gitignore
└── .env.example
```
