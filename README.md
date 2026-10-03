# LearnLens

LearnLens is an AI-powered study assistant for a student working from their own course materials.

## Purpose

LearnLens will let a student upload study material, such as PDFs, and ask questions about that material. Answers are planned to come from the uploaded documents, with the sources and pages used for each answer shown beside the response.

## Problem statement

Coursework often lives in long readings, lecture slides, and notes. Finding a specific explanation means searching those files by hand. A general chat tool can also answer with confidence when the course material does not support the claim. LearnLens is planned to keep each answer tied to the student's documents and to state when those documents do not contain enough evidence.

## Intended user

The intended user is a student who studies from personal course materials and wants help with reading, review, and exam preparation. The first person this project is being built for is a real student and friend.

## Planned technology stack

| Area | Choice |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Language model | Gemma, an open-weight model |
| Embeddings | An open-source embedding model |
| Data | PostgreSQL, pgvector |
| Deployment | Render |
| Version control | GitHub |

## High-level architecture

The browser client is a Next.js application. It will call a FastAPI backend that owns document ingestion, retrieval, and answer generation. PostgreSQL with pgvector will store document chunks and their embeddings. Gemma will generate an answer from the retrieved passages.

A fuller description of the planned design is in [docs/architecture.md](docs/architecture.md).

This stage initializes the repository. The API exposes `GET /api/v1/health`. Ingestion, embeddings, retrieval, model inference, authentication, and the database come in later stages.

## Planned RAG pipeline

1. Extract text from uploaded PDFs, keeping page references.
2. Split each document into meaningful chunks.
3. Generate embeddings with an open-source embedding model.
4. Store the embeddings in PostgreSQL with pgvector.
5. Embed the student's question and retrieve the most relevant chunks.
6. Pass those chunks to an open-weight Gemma model.
7. Return the answer together with the sources and pages that support it.
8. When the retrieved material is not sufficient, say so and withhold an unsupported answer.

Summaries, quizzes, explanations, and study insights are planned later, on the same document store.

## Why open-source AI is important

Study materials are personal. An open-weight model such as Gemma, paired with an open-source embedding model, keeps the assistant inspectable and avoids locking the project to one proprietary API. The models, prompts, and retrieval behavior can be reviewed, changed, and run in an environment this project controls. A student should be able to see how an answer was produced, and contributors should be able to reproduce the system.

## Planned grounding behavior

LearnLens will answer from retrieved passages in the student's documents. Each answer will cite the sources and pages that were used. When retrieval does not return enough relevant material, the assistant will say that the uploaded documents do not support an answer.

## Local development

### Frontend

From the repository root, in PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

The client runs at [http://localhost:3000](http://localhost:3000).

### Backend

From the repository root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS or Linux, activate the virtual environment with `source .venv/bin/activate` instead of the PowerShell command above.

The health check is [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health). A running API returns:

```json
{"status":"ok","service":"learnlens-api"}
```

### PostgreSQL + pgvector

Document chunks and embeddings persist in PostgreSQL with pgvector. See [docs/database.md](docs/database.md) for Docker setup, `DATABASE_URL`, Alembic migrations, and readiness checks (`GET /api/v1/ready`).

```powershell
docker compose up -d
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Copy `.env.example` files to local env files when configuration is needed. Do not commit those local files, and do not put real secrets in the examples.
