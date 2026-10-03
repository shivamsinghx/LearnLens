# Integration tests

Default `pytest` runs do **not** require PostgreSQL. They use an in-memory fake repository.

To exercise a real pgvector database manually:

1. `docker compose up -d` from the repo root
2. Configure `backend/.env` with `DATABASE_URL`
3. `alembic upgrade head`
4. Call `POST /api/v1/documents/{id}/embed` against a running API

Automated integration tests that need Docker can be added here later and marked with `@pytest.mark.integration`.
