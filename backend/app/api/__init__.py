"""HTTP routes for the LearnLens API."""

from fastapi import APIRouter

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.llm_ready import router as llm_ready_router
from app.api.qa import router as qa_router
from app.api.ready import router as ready_router
from app.api.retrieval import router as retrieval_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(ready_router)
router.include_router(llm_ready_router)
router.include_router(documents_router)
router.include_router(retrieval_router)
router.include_router(qa_router)
