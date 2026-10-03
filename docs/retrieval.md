# LearnLens semantic retrieval

Phase 2.6 adds question → evidence retrieval over pgvector. Grounded answers are in Phase 2.7 — see [qa.md](qa.md).

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
Embed
 ↓
PostgreSQL + pgvector
 ↓
Question
 ↓
Question embedding  (same model: EMBEDDING_MODEL / BAAI/bge-small-en-v1.5)
 ↓
Cosine similarity search  (HNSW: document_chunks_embedding_cosine_idx)
 ↓
Relevant chunks (+ provenance)
```

## Endpoint

`POST /api/v1/retrieval/search`

### Request

```json
{
  "query": "What is database normalization?",
  "document_id": "optional-document-id",
  "top_k": 5
}
```

| Field | Rules |
| --- | --- |
| `query` | Required, non-blank |
| `document_id` | Optional; when set, search only that document's chunks (filter in SQL) |
| `top_k` | Default **5**, maximum **10** |

### Response

```json
{
  "query": "What is database normalization?",
  "retrieval_status": "ok",
  "results": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "filename": "DBMS Notes.pdf",
      "chunk_index": 0,
      "page_start": 14,
      "page_end": 15,
      "text": "...",
      "similarity": 0.86
    }
  ]
}
```

`similarity` is a cosine similarity score (`1 - cosine_distance` on L2-normalized vectors). It is **not** calibrated confidence.

When nothing passes the threshold:

```json
{
  "query": "...",
  "results": [],
  "retrieval_status": "insufficient_evidence",
  "detail": "No chunks met the minimum similarity threshold (0.3)."
}
```

No answer text is generated in this phase.

## Configuration

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
RETRIEVAL_MIN_SIMILARITY=0.3
```

`RETRIEVAL_MIN_SIMILARITY` must be tuned with evaluation data. The default `0.3` is a starting point only.

## Database query

- Operator: pgvector cosine distance on `document_chunks.embedding`
- Ordering: ascending distance (highest similarity first)
- Index used: `document_chunks_embedding_cosine_idx` (HNSW, `vector_cosine_ops`)
- Filtering by `document_id` happens in SQL, not in Python

## Provenance

Every hit includes `document_id`, `filename`, `chunk_id`, `chunk_index`, `page_start`, `page_end`, and `text` so later answers can cite sources such as **DBMS Notes — Page 14**.
