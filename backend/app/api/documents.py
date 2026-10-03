"""Document upload routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.documents import (
    DocumentMetadata,
    DocumentUploadError,
    DocumentUploadResponse,
)
from app.services.document_storage import DocumentStorage
from app.utils.pdf import (
    MAX_FILE_BYTES,
    MAX_FILES_PER_BATCH,
    is_pdf_bytes,
    looks_like_pdf_filename,
)

router = APIRouter(prefix="/documents", tags=["documents"])
storage = DocumentStorage()


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
            # Still allow if magic + extension check out; otherwise reject.
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
