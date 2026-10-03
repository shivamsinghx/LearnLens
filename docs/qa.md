# LearnLens grounded Q&A (Gemma via Ollama)

Phase 2.7 adds retrieval-grounded answer generation. Source citation UI is deferred to Phase 2.8.

## Pipeline

```text
PDF
 ↓
Extract
 ↓
Chunk
 ↓
BGE Embeddings
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

## Model

| Setting | Default |
| --- | --- |
| `LLM_PROVIDER` | `ollama` |
| `LLM_MODEL` | `gemma3:4b` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |

Change `LLM_MODEL` if you pull a different Gemma tag (for example `gemma3:1b` or `gemma2:2b`). Do not hard-code the model name in application code.

The backend does **not** download models on startup. Pull models with the Ollama CLI.

## Local Ollama setup

1. Install Ollama from [https://ollama.com](https://ollama.com).
2. Start Ollama (desktop app or `ollama serve`).
3. Pull the configured model:

```powershell
ollama pull gemma3:4b
```

4. Copy `backend/.env.example` to `backend/.env` and adjust `LLM_MODEL` if needed.
5. Start the LearnLens backend as usual (`uvicorn app.main:app ...`).

Readiness check (independent of `/api/v1/health` and `/api/v1/ready`):

`GET /api/v1/llm/ready`

## Endpoint

`POST /api/v1/qa/ask`

### Request

```json
{
  "query": "What is database normalization?",
  "document_id": "optional-document-id",
  "top_k": 5
}
```

### Successful response

```json
{
  "query": "What is database normalization?",
  "answer": "...",
  "retrieval_status": "ok",
  "model": "gemma3:4b"
}
```

### Insufficient evidence

When semantic retrieval returns `insufficient_evidence`, **Gemma is not called**:

```json
{
  "query": "...",
  "answer": "I couldn't find enough information in your uploaded study material to answer this reliably.",
  "retrieval_status": "insufficient_evidence",
  "model": null
}
```

Source citations are retained internally by the QA orchestration layer for Phase 2.8 but are not exposed in this response yet.

## Grounding rules

- Retrieved chunks are the only authoritative context.
- Document text is delimited as untrusted content so prompt-injection phrases inside PDFs cannot override system instructions.
- Outside knowledge must not fill gaps.
- Fabricated page numbers / sources are forbidden.
- Application-level retrieval threshold/status gates generation (prompt instructions alone are not enough).

## Errors (user-safe)

| Condition | Typical status |
| --- | --- |
| Empty query | 422 |
| Document not found | 404 |
| Retrieval / DB failure | 503 |
| Ollama unavailable | 503 |
| Model not installed | 503 |
| LLM timeout | 504 |
| Generation failure | 502 |

Responses never expose stack traces, internal URLs, credentials, or raw exception dumps.

## Tests

Unit/API tests mock the Ollama boundary (no real model required):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Optional live Gemma integration (requires Ollama + pulled model + reachable DB for full PDF E2E):

```powershell
pytest -q -m llm
```

Or run the smoke script:

```powershell
$env:PYTHONPATH = "."
python scripts/smoke_qa_ollama.py
```
