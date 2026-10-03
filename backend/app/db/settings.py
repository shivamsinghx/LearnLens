"""Database and vector configuration (env-driven, no secrets in code)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env for local development (no-op if the file is absent).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Matches BAAI/bge-small-en-v1.5 unless overridden.
DEFAULT_EMBEDDING_DIMENSION = 384

# Minimum cosine similarity for returned chunks. Tune with evaluation data;
# 0.3 is a conservative starting point, not a scientifically optimal default.
DEFAULT_RETRIEVAL_MIN_SIMILARITY = 0.3


def get_database_url() -> str:
    """Return DATABASE_URL or raise a clear configuration error."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set DATABASE_URL to a PostgreSQL connection string before using "
            "database persistence (for example via backend/.env)."
        )
    return url


def get_embedding_dimension() -> int:
    """Return the configured embedding vector size."""
    raw = os.getenv("EMBEDDING_DIMENSION", "").strip()
    if not raw:
        return DEFAULT_EMBEDDING_DIMENSION
    try:
        dimension = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            "EMBEDDING_DIMENSION must be a positive integer "
            f"(got {raw!r})."
        ) from exc
    if dimension < 1:
        raise RuntimeError("EMBEDDING_DIMENSION must be >= 1.")
    return dimension


def get_retrieval_min_similarity() -> float:
    """Return the configured minimum cosine similarity for retrieval hits."""
    raw = os.getenv("RETRIEVAL_MIN_SIMILARITY", "").strip()
    if not raw:
        return DEFAULT_RETRIEVAL_MIN_SIMILARITY
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(
            "RETRIEVAL_MIN_SIMILARITY must be a number between 0 and 1 "
            f"(got {raw!r})."
        ) from exc
    if not 0.0 <= value <= 1.0:
        raise RuntimeError("RETRIEVAL_MIN_SIMILARITY must be between 0 and 1.")
    return value
