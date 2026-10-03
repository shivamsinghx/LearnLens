# Integration tests

Default `pytest` runs unit/API tests with fakes. Integration tests under this folder are marked and **skip** when their dependencies are unreachable.

## PostgreSQL + pgvector (`@pytest.mark.integration`)

1. `docker compose up -d` from the repo root
2. Configure `backend/.env` with `DATABASE_URL`
3. `alembic upgrade head`
4. `pytest -q` (or `pytest -q tests/integration`)

## Live Gemma / Ollama (`@pytest.mark.llm`)

Requires a running Ollama process and the configured model (default `gemma3:4b`):

```powershell
ollama pull gemma3:4b
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q -m llm
```

Full PDF → retrieval → Gemma smoke (also needs PostgreSQL):

```powershell
$env:PYTHONPATH = "."
python scripts/smoke_qa_ollama.py
```
