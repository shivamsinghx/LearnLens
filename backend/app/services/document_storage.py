"""Persist uploaded PDFs with unique IDs and sidecar metadata."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models.documents import ChunkedDocument, DocumentMetadata, ExtractedDocument
from app.utils.pdf import sanitize_filename


def default_upload_dir() -> Path:
    configured = os.getenv("UPLOAD_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "storage" / "uploads").resolve()


class DocumentStorage:
    def __init__(self, upload_dir: Path | None = None) -> None:
        self.upload_dir = upload_dir or default_upload_dir()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, document_id: str) -> Path:
        return self.upload_dir / f"{document_id}.json"

    def _extraction_path(self, document_id: str) -> Path:
        return self.upload_dir / f"{document_id}.extracted.json"

    def _chunks_path(self, document_id: str) -> Path:
        return self.upload_dir / f"{document_id}.chunks.json"

    def save_pdf(self, *, original_filename: str, content: bytes) -> DocumentMetadata:
        document_id = str(uuid.uuid4())
        safe_name = sanitize_filename(original_filename)
        stored_filename = f"{document_id}_{safe_name}"
        pdf_path = self.upload_dir / stored_filename
        meta_path = self._meta_path(document_id)

        pdf_path.write_bytes(content)

        uploaded_at = datetime.now(timezone.utc)
        metadata = DocumentMetadata(
            id=document_id,
            filename=Path(original_filename).name or safe_name,
            size_bytes=len(content),
            status="uploaded",
            uploaded_at=uploaded_at,
            stored_filename=stored_filename,
            extraction_status="pending",
        )
        meta_path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return metadata

    def get_metadata(self, document_id: str) -> DocumentMetadata | None:
        meta_path = self._meta_path(document_id)
        if not meta_path.is_file():
            return None
        return DocumentMetadata.model_validate_json(
            meta_path.read_text(encoding="utf-8")
        )

    def get_pdf_path(self, document_id: str) -> Path | None:
        metadata = self.get_metadata(document_id)
        if metadata is None:
            return None
        pdf_path = self.upload_dir / metadata.stored_filename
        if not pdf_path.is_file():
            return None
        return pdf_path

    def save_extraction(
        self,
        *,
        metadata: DocumentMetadata,
        extracted: ExtractedDocument,
        extraction_status: str,
        detail: str | None = None,
    ) -> DocumentMetadata:
        extraction_path = self._extraction_path(metadata.id)
        extraction_path.write_text(
            extracted.model_dump_json(indent=2),
            encoding="utf-8",
        )

        updated = metadata.model_copy(
            update={
                "status": (
                    "extracted" if extraction_status == "extracted" else "extraction_failed"
                ),
                "page_count": len(extracted.pages),
                "extraction_status": extraction_status,
                "extraction_detail": detail,
            }
        )
        self._meta_path(metadata.id).write_text(
            updated.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return updated

    def load_extraction(self, document_id: str) -> ExtractedDocument:
        """Load extracted JSON; raises FileNotFoundError or ValueError."""
        path = self._extraction_path(document_id)
        if not path.is_file():
            raise FileNotFoundError(document_id)
        return ExtractedDocument.model_validate_json(
            path.read_text(encoding="utf-8")
        )

    def get_extraction(self, document_id: str) -> ExtractedDocument | None:
        try:
            return self.load_extraction(document_id)
        except (FileNotFoundError, OSError, ValueError):
            return None

    def save_chunks(
        self,
        *,
        metadata: DocumentMetadata,
        chunked: ChunkedDocument,
        chunking_status: str,
        detail: str | None = None,
    ) -> DocumentMetadata:
        self._chunks_path(metadata.id).write_text(
            chunked.model_dump_json(indent=2),
            encoding="utf-8",
        )

        updated = metadata.model_copy(
            update={
                "status": "chunked" if chunking_status == "completed" else "chunking_failed",
                "chunk_count": len(chunked.chunks),
                "chunking_status": chunking_status,
                "chunking_detail": detail,
            }
        )
        self._meta_path(metadata.id).write_text(
            updated.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return updated

    def get_chunks(self, document_id: str) -> ChunkedDocument | None:
        path = self._chunks_path(document_id)
        if not path.is_file():
            return None
        try:
            return ChunkedDocument.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
