"""SQLAlchemy engine/session helpers for LearnLens."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.settings import get_database_url

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(*, force_new: bool = False) -> Engine:
    """Create (or reuse) the SQLAlchemy engine for DATABASE_URL."""
    global _engine, _session_factory
    if _engine is not None and not force_new:
        return _engine

    url = get_database_url()
    _engine = create_engine(url, pool_pre_ping=True)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_ready() -> dict[str, str]:
    """Verify PostgreSQL connectivity and that the vector extension exists."""
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        row = connection.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).first()
        if row is None:
            raise RuntimeError(
                "PostgreSQL is reachable but the pgvector extension is not installed. "
                "Run migrations or CREATE EXTENSION vector."
            )
    return {"database": "ok", "pgvector": "ok"}


def reset_engine() -> None:
    """Dispose the cached engine (used by tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
