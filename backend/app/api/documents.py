"""Document upload and extraction routes."""

from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.documents import (
    ChunkedDocument,
    DocumentChunkingResponse,
    DocumentExtractionResponse,
    DocumentMetadata,
    DocumentUploadError,
    DocumentUploadResponse,
    ExtractedDocument,
)
from app.services.document_chunking import DocumentChunkingService
from app.services.document_storage import DocumentStorage
from app.services.pdf_extraction import PdfExtractionError, PdfExtractionService
from app.utils.pdf import (
    MAX_FILE_BYTES,
    MAX_FILES_PER_BATCH,
    is_pdf_bytes,
    looks_like_pdf_filename,
)

router = APIRouter(prefix="/documents", tags=["documents"])
storage = DocumentStorage()
extractor = PdfExtractionService()
chunker = DocumentChunkingService()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    files: list[UploadFile] = File(..., description="One or more PDF files"),
) -> DocumentUploadResponse:
    """Accept PDF uploads over multipart/form-data and persist them on disk."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one PDF file is required.",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can upload up to {MAX_FILES_PER_BATCH} files per request.",
        )

    documents: list[DocumentMetadata] = []
    errors: list[DocumentUploadError] = []

    for upload in files:
        filename = upload.filename or "document.pdf"
        try:
            content = await upload.read()
        except Exception:
            errors.append(
                DocumentUploadError(
                    filename=filename,
                    detail="Could not read the uploaded file.",
                )
            )
            continue

        if len(content) == 0:
            errors.append(
                DocumentUploadError(
                    filename=filename,
                    detail="Empty files are not allowed.",
                )
            )
            continue

        if len(content) > MAX_FILE_BYTES:
            errors.append(
                DocumentUploadError(
                    filename=filename,
                    detail=f"File exceeds the {MAX_FILE_BYTES // (1024 * 1024)} MB size limit.",
                )
            )
            continue

        content_type = (upload.content_type or "").lower()
        if content_type and content_type not in {
            "application/pdf",
            "application/x-pdf",
            "binary/octet-stream",
            "application/octet-stream",
        }:
            if not (looks_like_pdf_filename(filename) and is_pdf_bytes(content)):
                errors.append(
                    DocumentUploadError(
                        filename=filename,
                        detail="Only PDF files are accepted.",
                    )
                )
                continue

        if not looks_like_pdf_filename(filename) or not is_pdf_bytes(content):
            errors.append(
                DocumentUploadError(
                    filename=filename,
                    detail="Only valid PDF files are accepted.",
                )
            )
            continue

        try:
            documents.append(
                storage.save_pdf(original_filename=filename, content=content)
            )
        except OSError:
            errors.append(
                DocumentUploadError(
                    filename=filename,
                    detail="Failed to store the uploaded file.",
                )
            )

    if not documents:
        detail = errors[0].detail if errors else "No valid PDF files were uploaded."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    return DocumentUploadResponse(documents=documents, errors=errors)


@router.post(
    "/{document_id}/extract",
    response_model=DocumentExtractionResponse,
)
def extract_document(document_id: str) -> DocumentExtractionResponse:
    """Extract page-level text from a previously uploaded PDF."""
    metadata = storage.get_metadata(document_id)
    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    pdf_path = storage.get_pdf_path(document_id)
    if pdf_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored PDF file is missing.",
        )

    try:
        result = extractor.extract_file(
            document_id=metadata.id,
            filename=metadata.filename,
            pdf_path=pdf_path,
        )
    except PdfExtractionError as exc:
        empty = ExtractedDocument(
            document_id=metadata.id,
            filename=metadata.filename,
            pages=[],
        )
        storage.save_extraction(
            metadata=metadata,
            extracted=empty,
            extraction_status="failed",
            detail=str(exc),
        )
        return DocumentExtractionResponse(
            document_id=metadata.id,
            filename=metadata.filename,
            page_count=0,
            extraction_status="failed",
            detail=str(exc),
            pages=[],
        )

    storage.save_extraction(
        metadata=metadata,
        extracted=result.document,
        extraction_status=result.status,
        detail=result.detail,
    )

    status_value = cast(
        Literal["extracted", "empty", "failed"],
        result.status,
    )
    return DocumentExtractionResponse(
        document_id=result.document.document_id,
        filename=result.document.filename,
        page_count=len(result.document.pages),
        extraction_status=status_value,
        detail=result.detail,
        pages=result.document.pages,
    )


@router.post(
    "/{document_id}/chunk",
    response_model=DocumentChunkingResponse,
)
def chunk_document(document_id: str) -> DocumentChunkingResponse:
    """Chunk previously extracted page-level text for later retrieval."""
    metadata = storage.get_metadata(document_id)
    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    try:
        extracted = storage.load_extraction(document_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extracted text not found. Run extraction first.",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=getattr(
                status,
                "HTTP_422_UNPROCESSABLE_CONTENT",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            detail="Extracted document JSON is invalid.",
        ) from None

    result = chunker.chunk_extracted(extracted)
    chunked = ChunkedDocument(
        document_id=metadata.id,
        filename=metadata.filename,
        chunks=result.chunks,
    )
    storage.save_chunks(
        metadata=metadata,
        chunked=chunked,
        chunking_status=result.status,
        detail=result.detail,
    )

    status_value = cast(
        Literal["completed", "empty", "failed"],
        result.status,
    )
    return DocumentChunkingResponse(
        document_id=metadata.id,
        chunk_count=len(result.chunks),
        chunking_status=status_value,
        detail=result.detail,
    )
