"""Orchestrate retrieval → context → Gemma for grounded answers.

Pipeline:
  question → embed → retrieve → (if ok) build context → Gemma → answer

Gemma is never called when retrieval_status is insufficient_evidence.
"""

from __future__ import annotations

from app.models.qa import INSUFFICIENT_EVIDENCE_ANSWER, AskResult
from app.services.context_builder import build_context
from app.services.llm_service import LLMError, LLMService
from app.services.retrieval_service import RetrievalError, RetrievalService


class QAError(Exception):
    """Domain error for QA failures that map to HTTP responses."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class QAService:
    """Grounded question-answering over retrieved study material."""

    def __init__(
        self,
        *,
        retriever: RetrievalService | None = None,
        llm: LLMService | None = None,
    ) -> None:
        self.retriever = retriever or RetrievalService()
        self.llm = llm or LLMService()

    def ask(
        self,
        query: str,
        *,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> AskResult:
        cleaned = (query or "").strip()
        if not cleaned:
            raise QAError("query must not be empty.", status_code=422)

        try:
            retrieval = self.retriever.search(
                cleaned,
                document_id=document_id,
                top_k=top_k,
            )
        except RetrievalError as exc:
            raise QAError(str(exc), status_code=exc.status_code) from exc

        if retrieval.retrieval_status == "insufficient_evidence":
            return AskResult(
                query=cleaned,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                retrieval_status="insufficient_evidence",
                model=None,
                sources=[],
            )

        context = build_context(retrieval.results)

        try:
            answer = self.llm.generate_answer(context=context, question=cleaned)
        except LLMError as exc:
            raise QAError(str(exc), status_code=exc.status_code) from exc
        except Exception as exc:  # noqa: BLE001
            raise QAError(
                "Answer generation failed.",
                status_code=502,
            ) from exc

        return AskResult(
            query=cleaned,
            answer=answer,
            retrieval_status="ok",
            model=self.llm.model_name,
            sources=list(retrieval.results),
        )
