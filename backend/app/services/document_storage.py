"""Persist uploaded PDFs with unique IDs and sidecar metadata."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models.documents import DocumentMetadata
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

    def save_pdf(self, *, original_filename: str, content: bytes) -> DocumentMetadata:
        document_id = str(uuid.uuid4())
        safe_name = sanitize_filename(original_filename)
        stored_filename = f"{document_id}_{safe_name}"
        pdf_path = self.upload_dir / stored_filename
        meta_path = self.upload_dir / f"{document_id}.json"

        pdf_path.write_bytes(content)

        uploaded_at = datetime.now(timezone.utc)
        metadata = DocumentMetadata(
            id=document_id,
            filename=Path(original_filename).name or safe_name,
            size_bytes=len(content),
            status="uploaded",
            uploaded_at=uploaded_at,
            stored_filename=stored_filename,
        )
        meta_path.write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return metadata
