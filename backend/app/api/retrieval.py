"""Semantic retrieval routes (question → evidence chunks)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.retrieval import RetrievalSearchRequest, RetrievalSearchResponse
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalError, RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

# Injected by tests; production constructs on first use.
retriever: RetrievalService | None = None


def get_retriever() -> RetrievalService:
    global retriever
    if retriever is None:
        retriever = RetrievalService(embedder=EmbeddingService())
    return retriever


@router.post("/search", response_model=RetrievalSearchResponse)
def search_chunks(body: RetrievalSearchRequest) -> RetrievalSearchResponse:
    """Embed a question and return the most similar document chunks."""
    try:
        return get_retriever().search(
            body.query,
            document_id=body.document_id,
            top_k=body.top_k,
        )
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
