from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Report that the LearnLens API process is running."""
    return {"status": "ok", "service": "learnlens-api"}
