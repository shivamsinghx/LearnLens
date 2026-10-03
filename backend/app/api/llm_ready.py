"""LLM readiness probe (Ollama + configured Gemma model).

Independent of GET /api/v1/health and GET /api/v1/ready so database
readiness does not require Gemma to be running.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.services.llm_service import LLMError, LLMService

router = APIRouter(tags=["health"])

# Injected by tests; production constructs on first use.
llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service


@router.get("/llm/ready")
def llm_ready() -> dict[str, str]:
    """Verify the configured Ollama service and Gemma model are reachable."""
    try:
        return get_llm_service().check_ready()
    except LLMError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=str(exc),
        ) from exc
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The language model service is unavailable.",
        )
