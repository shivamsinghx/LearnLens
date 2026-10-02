# LearnLens architecture

This document describes the planned LearnLens architecture. The current repository contains the project layout, a Next.js client, and a FastAPI health check.

## Overview

LearnLens is a study assistant. A student will use a web client to upload course material and ask questions about it. The API will retrieve relevant passages from that material and ask an open-weight model to answer from those passages.

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
        +-- Document ingestion (planned)
        +-- Retrieval (planned)
        +-- Answer generation with Gemma (planned)
        |
        v
PostgreSQL + pgvector (planned)
```

## Components

### Frontend

The frontend is a Next.js application in `frontend/`. It uses TypeScript and Tailwind CSS.

Planned responsibilities:

- Upload study files such as PDFs.
- Submit questions about those files.
- Show the answer with the source pages used to produce it.
- Later, present summaries, quizzes, explanations, and study insights.

### Backend

The backend is a FastAPI application in `backend/app/`.

| Path | Role |
| --- | --- |
| `main.py` | Application entrypoint |
| `api/` | HTTP routes |
| `services/` | Application services (planned) |
| `models/` | Request and response models (planned) |
| `rag/` | Ingestion, chunking, embeddings, and retrieval (planned) |
| `utils/` | Shared helpers (planned) |

The implemented route is `GET /api/v1/health`. It returns JSON confirming that the API process is running.

### Data

PostgreSQL with the pgvector extension is the planned store for document chunks and embeddings. Database setup is reserved for a later stage.

### Models

An open-source embedding model will turn document chunks and questions into vectors. An open-weight Gemma model will write answers from the retrieved chunks. Neither model is installed in this stage.

## Planned request flow

1. The student uploads a PDF.
2. The API extracts the text and keeps page references.
3. The text is split into meaningful chunks.
4. Each chunk is embedded and stored with pgvector.
5. The question is embedded and matched against stored chunks.
6. The relevant chunks are passed to Gemma with instructions to answer from that evidence.
7. The response includes the answer and the sources and pages that support it.
8. When the retrieved material is not enough to support an answer, the API says so.

## Deployment

The frontend and API are planned for deployment on Render, with managed PostgreSQL and pgvector for document storage. Deployment configuration is reserved for a later stage.

## Repository layout

```text
LearnLens/
├── frontend/          Next.js client
├── backend/           FastAPI application
├── docs/              Architecture and project notes
├── README.md
├── .gitignore
└── .env.example
```
