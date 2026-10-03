"""Request/response models for document upload."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    size_bytes: int = Field(ge=0)
    status: Literal["uploaded"] = "uploaded"
    uploaded_at: datetime
    stored_filename: str


class DocumentUploadError(BaseModel):
    filename: str
    detail: str


class DocumentUploadResponse(BaseModel):
    documents: list[DocumentMetadata]
    errors: list[DocumentUploadError] = Field(default_factory=list)
