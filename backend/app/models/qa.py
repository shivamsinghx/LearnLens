"""Request/response models for grounded question answering."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.retrieval import DEFAULT_TOP_K, MAX_TOP_K, RetrievalResult

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I couldn't find enough information in your uploaded study material "
    "to answer this reliably."
)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_id: str | None = None
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query must not be empty.")
        return cleaned


class AskResponse(BaseModel):
    """Public QA response. Source citations are deferred to Phase 2.8."""

    query: str
    answer: str
    retrieval_status: Literal["ok", "insufficient_evidence"]
    model: str | None = None


class AskResult(BaseModel):
    """Internal orchestration result retaining retrieval provenance for Phase 2.8."""

    query: str
    answer: str
    retrieval_status: Literal["ok", "insufficient_evidence"]
    model: str | None = None
    sources: list[RetrievalResult] = Field(default_factory=list)

    def to_public(self) -> AskResponse:
        return AskResponse(
            query=self.query,
            answer=self.answer,
            retrieval_status=self.retrieval_status,
            model=self.model,
        )
