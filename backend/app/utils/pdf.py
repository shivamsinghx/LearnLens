"""PDF upload validation helpers."""

from __future__ import annotations

import re
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES_PER_BATCH = 5
PDF_MAGIC = b"%PDF"
_SAFE_NAME_RE = re.compile(r"[^\w.\- ]+", re.UNICODE)


def is_pdf_bytes(data: bytes) -> bool:
    """Return True when the payload starts with the PDF magic header."""
    return data[:4] == PDF_MAGIC


def looks_like_pdf_filename(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() == ".pdf"


def sanitize_filename(filename: str | None) -> str:
    """Return a filesystem-safe basename, always ending in .pdf."""
    raw = Path(filename or "document.pdf").name
    cleaned = _SAFE_NAME_RE.sub("_", raw).strip(". ")
    if not cleaned:
        cleaned = "document.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"
    return cleaned[:180]
