"""Request/response models for document upload and extraction."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    size_bytes: int = Field(ge=0)
    status: Literal["uploaded", "extracted", "extraction_failed"] = "uploaded"
    uploaded_at: datetime
    stored_filename: str
    page_count: int | None = None
    extraction_status: Literal["pending", "extracted", "empty", "failed"] | None = None
    extraction_detail: str | None = None


class DocumentUploadError(BaseModel):
    filename: str
    detail: str


class DocumentUploadResponse(BaseModel):
    documents: list[DocumentMetadata]
    errors: list[DocumentUploadError] = Field(default_factory=list)


class ExtractedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class ExtractedDocument(BaseModel):
    document_id: str
    filename: str
    pages: list[ExtractedPage]


class DocumentExtractionResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int = Field(ge=0)
    extraction_status: Literal["extracted", "empty", "failed"]
    detail: str | None = None
    pages: list[ExtractedPage] = Field(default_factory=list)
