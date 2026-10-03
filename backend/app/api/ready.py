"""Readiness probe for API + PostgreSQL/pgvector."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.db.database import check_database_ready

router = APIRouter(tags=["health"])


@router.get("/ready")
def ready() -> dict[str, str]:
    """Verify the API can reach PostgreSQL with pgvector enabled."""
    try:
        checks = check_database_ready()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness check failed: {exc}",
        ) from exc

    return {
        "status": "ready",
        "service": "learnlens-api",
        "database": checks["database"],
        "pgvector": checks["pgvector"],
    }
