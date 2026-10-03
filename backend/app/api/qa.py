"""Grounded Q&A routes (retrieval → Gemma)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.qa import AskRequest, AskResponse
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.qa_service import QAError, QAService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/qa", tags=["qa"])

# Injected by tests; production constructs on first use.
qa_service: QAService | None = None


def get_qa_service() -> QAService:
    global qa_service
    if qa_service is None:
        qa_service = QAService(
            retriever=RetrievalService(embedder=EmbeddingService()),
            llm=LLMService(),
        )
    return qa_service


@router.post("/ask", response_model=AskResponse)
def ask_question(body: AskRequest) -> AskResponse:
    """Retrieve evidence and generate a grounded answer with Gemma."""
    try:
        result = get_qa_service().ask(
            body.query,
            document_id=body.document_id,
            top_k=body.top_k,
        )
    except QAError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return result.to_public()
