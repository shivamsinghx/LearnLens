"""Page-preserving PDF text extraction with PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from app.models.documents import ExtractedDocument, ExtractedPage
from app.utils.text_normalize import has_meaningful_text, normalize_page_text


@dataclass(frozen=True)
class ExtractionResult:
    document: ExtractedDocument
    status: str  # extracted | empty | failed
    detail: str | None = None


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be opened or read for extraction."""


class PdfExtractionService:
    """Extract text page-by-page while preserving page boundaries."""

    def extract_file(
        self,
        *,
        document_id: str,
        filename: str,
        pdf_path: Path,
    ) -> ExtractionResult:
        if not pdf_path.is_file():
            raise PdfExtractionError("Stored PDF file is missing.")

        try:
            document = fitz.open(pdf_path)
        except Exception as exc:  # noqa: BLE001 - surface corrupt PDFs cleanly
            raise PdfExtractionError("The PDF could not be opened for text extraction.") from exc

        try:
            if document.page_count == 0:
                empty = ExtractedDocument(
                    document_id=document_id,
                    filename=filename,
                    pages=[],
                )
                return ExtractionResult(
                    document=empty,
                    status="empty",
                    detail="This PDF has no pages with extractable text.",
                )

            pages: list[ExtractedPage] = []
            page_texts: list[str] = []
            for index in range(document.page_count):
                page = document.load_page(index)
                raw = page.get_text("text") or ""
                normalized = normalize_page_text(raw)
                page_number = index + 1
                pages.append(ExtractedPage(page_number=page_number, text=normalized))
                page_texts.append(normalized)

            extracted = ExtractedDocument(
                document_id=document_id,
                filename=filename,
                pages=pages,
            )

            if not has_meaningful_text(page_texts):
                return ExtractionResult(
                    document=extracted,
                    status="empty",
                    detail=(
                        "No meaningful extractable text was found. "
                        "The PDF may be scanned or image-only."
                    ),
                )

            return ExtractionResult(document=extracted, status="extracted")
        finally:
            document.close()
