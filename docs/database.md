# LearnLens database (PostgreSQL + pgvector)

Phase 2.5 makes **PostgreSQL + pgvector** the primary store for documents, chunks, and embeddings.

Filesystem JSON sidecars (`{document_id}.chunks.json`, `{document_id}.embeddings.json`) are still written temporarily and can be removed after Phase 2.6 semantic retrieval is verified.

## Pipeline

```text
PDF
 ↓
Upload
 ↓
Extract
 ↓
Chunk
 ↓
Embed  (BAAI/bge-small-en-v1.5 → 384-d L2-normalized)
 ↓
PostgreSQL + pgvector
 ↓
Question → question embedding → cosine search → relevant chunks
 ↓
[Gemma grounded answers — LATER]
```

See also [retrieval.md](retrieval.md).

## 1. Start PostgreSQL + pgvector locally

From the repository root:

```powershell
docker compose up -d
```

This starts `pgvector/pgvector:pg16` with:

| Setting | Value |
| --- | --- |
| user | `learnlens` |
| password | `learnlens` |
| database | `learnlens` |
| port | `5432` |

## 2. Configure `DATABASE_URL`

Copy `backend/.env.example` to `backend/.env` and ensure:

```env
DATABASE_URL=postgresql+psycopg://learnlens:learnlens@127.0.0.1:5432/learnlens
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
```

Do not commit `.env` or real secrets.

If `DATABASE_URL` is missing when database code runs, the API fails with a clear configuration error.

## 3. Run migrations

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
```

The initial migration:

- enables `CREATE EXTENSION IF NOT EXISTS vector`
- creates `documents` and `document_chunks`
- defines `embedding vector(384)`
- adds FK cascade `document_chunks.document_id → documents.id`
- creates an HNSW cosine index for future Phase 2.6 search (unused by APIs in this phase)

## 4. Verify pgvector

```powershell
docker compose exec db psql -U learnlens -d learnlens -c "\dx"
```

You should see the `vector` extension.

Readiness probe (API must be running and `DATABASE_URL` set):

```text
GET http://127.0.0.1:8000/api/v1/ready
```

Existing liveness probe is unchanged:

```text
GET http://127.0.0.1:8000/api/v1/health
```

## 5. Run tests

Unit/API tests (no Docker required; repository is faked):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Optional live-database checks: start Docker, migrate, then run any future tests under `tests/integration/` (none required for the default suite).

## Schema (conceptual)

**documents:** `id`, `filename`, `size`, `content_type`, `status`, `created_at`, `updated_at`

**document_chunks:** `id` (pipeline `chunk_id`), `document_id`, `chunk_index`, `page_start`, `page_end`, `text`, `character_count`, `embedding vector(384)`, `embedding_model`, `created_at`

Document IDs from upload are reused end-to-end — no second ID is generated for the database row.
