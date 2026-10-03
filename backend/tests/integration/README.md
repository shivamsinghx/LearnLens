# Integration tests

Default `pytest` runs unit/API tests with fakes. Integration tests under this folder are marked `@pytest.mark.integration` and **skip** when PostgreSQL is unreachable.

To run them against Docker:

1. `docker compose up -d` from the repo root
2. Configure `backend/.env` with `DATABASE_URL`
3. `alembic upgrade head`
4. `pytest -q` (or `pytest -q tests/integration`)
