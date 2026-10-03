import pytest

from app.db.database import reset_engine
from app.db.settings import (
    DEFAULT_EMBEDDING_DIMENSION,
    get_database_url,
    get_embedding_dimension,
)


def test_database_url_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine()
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()


def test_database_url_reads_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://learnlens:learnlens@127.0.0.1:5432/learnlens",
    )
    assert "postgresql+psycopg://" in get_database_url()


def test_embedding_dimension_default_and_override(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIMENSION", raising=False)
    assert get_embedding_dimension() == DEFAULT_EMBEDDING_DIMENSION
    assert get_embedding_dimension() == 384

    monkeypatch.setenv("EMBEDDING_DIMENSION", "384")
    assert get_embedding_dimension() == 384

    monkeypatch.setenv("EMBEDDING_DIMENSION", "not-a-number")
    with pytest.raises(RuntimeError, match="EMBEDDING_DIMENSION"):
        get_embedding_dimension()
