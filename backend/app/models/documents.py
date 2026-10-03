"""Request/response models for document upload, extraction, chunking, and embeddings."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    size_bytes: int = Field(ge=0)
    status: Literal[
        "uploaded",
        "extracted",
        "extraction_failed",
        "chunked",
        "chunking_failed",
        "embedded",
        "embedding_failed",
    ] = "uploaded"
    uploaded_at: datetime
    stored_filename: str
    page_count: int | None = None
    extraction_status: Literal["pending", "extracted", "empty", "failed"] | None = None
    extraction_detail: str | None = None
    chunk_count: int | None = None
    chunking_status: Literal["pending", "completed", "empty", "failed"] | None = None
    chunking_detail: str | None = None
    embedding_status: Literal["pending", "completed", "empty", "failed"] | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None
    embedding_detail: str | None = None


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


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    text: str
    character_count: int = Field(ge=0)


class ChunkedDocument(BaseModel):
    document_id: str
    filename: str
    chunks: list[DocumentChunk]


class DocumentChunkingResponse(BaseModel):
    document_id: str
    chunk_count: int = Field(ge=0)
    chunking_status: Literal["completed", "empty", "failed"]
    detail: str | None = None


class EmbeddedChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    text: str
    character_count: int = Field(ge=0)
    embedding: list[float]
    embedding_model: str


class EmbeddedDocument(BaseModel):
    document_id: str
    filename: str
    embedding_model: str
    embedding_dimension: int = Field(ge=0)
    chunks: list[EmbeddedChunk]


class DocumentEmbeddingResponse(BaseModel):
    document_id: str
    chunk_count: int = Field(ge=0)
    embedding_dimension: int = Field(ge=0)
    embedding_model: str
    embedding_status: Literal["completed", "empty", "failed"]
    detail: str | None = None
