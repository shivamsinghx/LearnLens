"""Request/response models for semantic retrieval."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

DEFAULT_TOP_K = 5
MAX_TOP_K = 10


class RetrievalSearchRequest(BaseModel):
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


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int = Field(ge=0)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    text: str
    similarity: float


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalResult] = Field(default_factory=list)
    retrieval_status: Literal["ok", "insufficient_evidence"]
    detail: str | None = None
