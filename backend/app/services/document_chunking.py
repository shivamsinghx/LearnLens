"""Paragraph-aware document chunking with recoverable page provenance."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.documents import DocumentChunk, ExtractedDocument

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ChunkingConfig:
    """Tunable chunking parameters (character-based, no tokenizer)."""

    target_chunk_size: int = 1200
    max_chunk_size: int = 1500
    overlap: int = 200

    def __post_init__(self) -> None:
        if self.target_chunk_size < 1:
            raise ValueError("target_chunk_size must be >= 1")
        if self.max_chunk_size < self.target_chunk_size:
            raise ValueError("max_chunk_size must be >= target_chunk_size")
        if self.overlap < 0:
            raise ValueError("overlap must be >= 0")
        if self.overlap >= self.target_chunk_size:
            raise ValueError("overlap must be smaller than target_chunk_size")


@dataclass(frozen=True)
class _Paragraph:
    text: str
    page: int


@dataclass(frozen=True)
class ChunkingResult:
    chunks: list[DocumentChunk]
    status: str  # completed | empty
    detail: str | None = None


def _split_paragraphs(page_text: str, page_number: int) -> list[_Paragraph]:
    if not page_text or not page_text.strip():
        return []
    parts = re.split(r"\n\s*\n", page_text.strip())
    paragraphs: list[_Paragraph] = []
    for part in parts:
        cleaned = part.strip()
        if cleaned:
            paragraphs.append(_Paragraph(text=cleaned, page=page_number))
    return paragraphs


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [part.strip() for part in parts if part.strip()]


def _overlap_prefix(previous: str, overlap: int) -> str:
    if overlap <= 0 or not previous:
        return ""
    if len(previous) <= overlap:
        snippet = previous
    else:
        snippet = previous[-overlap:]
        # Prefer starting at a word boundary when possible.
        space = snippet.find(" ")
        if 0 < space < len(snippet) - 1:
            snippet = snippet[space + 1 :]
    return snippet.strip()


def _hard_split(text: str, max_size: int) -> list[str]:
    """Last-resort split on word boundaries, then hard cut if needed."""
    if len(text) <= max_size:
        return [text]

    pieces: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_size:
            pieces.append(remaining)
            break
        window = remaining[:max_size]
        split_at = window.rfind(" ")
        if split_at < max_size // 4:
            split_at = max_size
        piece = remaining[:split_at].rstrip()
        if not piece:
            piece = remaining[:max_size]
            split_at = len(piece)
        pieces.append(piece)
        remaining = remaining[split_at:].lstrip()
    return pieces


def _split_long_paragraph(
    text: str,
    *,
    target: int,
    max_size: int,
    overlap: int,
) -> list[str]:
    sentences = _split_sentences(text)
    if len(sentences) <= 1 and len(text) > max_size:
        base = _hard_split(text, max_size)
    else:
        base = []
        current = ""
        for sentence in sentences:
            if not current:
                if len(sentence) > max_size:
                    base.extend(_hard_split(sentence, max_size))
                    continue
                current = sentence
                continue

            candidate = f"{current} {sentence}"
            if len(candidate) <= target:
                current = candidate
            elif len(candidate) <= max_size:
                current = candidate
            else:
                base.append(current)
                if len(sentence) > max_size:
                    base.extend(_hard_split(sentence, max_size))
                    current = ""
                else:
                    current = sentence
        if current:
            base.append(current)

    if overlap <= 0 or len(base) <= 1:
        return base

    with_overlap: list[str] = [base[0]]
    for index in range(1, len(base)):
        prefix = _overlap_prefix(base[index - 1], overlap)
        piece = base[index]
        if prefix and not piece.startswith(prefix):
            combined = f"{prefix} {piece}".strip()
            if len(combined) > max_size + overlap:
                # Keep the piece intact if overlap would blow the budget badly.
                with_overlap.append(piece)
            else:
                with_overlap.append(combined)
        else:
            with_overlap.append(piece)
    return with_overlap


class DocumentChunkingService:
    """Turn page-level extracted text into retrieval-ready chunks."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def chunk_extracted(self, extracted: ExtractedDocument) -> ChunkingResult:
        paragraphs: list[_Paragraph] = []
        for page in extracted.pages:
            paragraphs.extend(_split_paragraphs(page.text, page.page_number))

        if not paragraphs:
            return ChunkingResult(
                chunks=[],
                status="empty",
                detail="No chunkable text was found in the extracted document.",
            )

        cfg = self.config
        chunks: list[DocumentChunk] = []
        current_texts: list[str] = []
        current_pages: list[int] = []
        current_len = 0

        def flush() -> None:
            nonlocal current_texts, current_pages, current_len
            if not current_texts:
                return
            text = "\n\n".join(current_texts).strip()
            if not text:
                current_texts = []
                current_pages = []
                current_len = 0
                return
            index = len(chunks)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{extracted.document_id}-chunk-{index}",
                    document_id=extracted.document_id,
                    chunk_index=index,
                    page_start=min(current_pages),
                    page_end=max(current_pages),
                    text=text,
                    character_count=len(text),
                )
            )
            current_texts = []
            current_pages = []
            current_len = 0

        def emit_text(text: str, page: int) -> None:
            nonlocal current_texts, current_pages, current_len
            separator = 2 if current_texts else 0
            projected = current_len + separator + len(text)

            if current_texts and projected > cfg.max_chunk_size:
                flush()
                separator = 0
                projected = len(text)

            if not current_texts and len(text) > cfg.max_chunk_size:
                pieces = _split_long_paragraph(
                    text,
                    target=cfg.target_chunk_size,
                    max_size=cfg.max_chunk_size,
                    overlap=cfg.overlap,
                )
                for piece in pieces:
                    current_texts = [piece]
                    current_pages = [page]
                    current_len = len(piece)
                    flush()
                return

            if current_texts and projected > cfg.target_chunk_size:
                # Allow modest growth up to max; otherwise start a new chunk.
                if projected > cfg.max_chunk_size:
                    flush()

            current_texts.append(text)
            current_pages.append(page)
            current_len = len("\n\n".join(current_texts))

        for paragraph in paragraphs:
            if len(paragraph.text) > cfg.max_chunk_size:
                flush()
                pieces = _split_long_paragraph(
                    paragraph.text,
                    target=cfg.target_chunk_size,
                    max_size=cfg.max_chunk_size,
                    overlap=cfg.overlap,
                )
                for piece in pieces:
                    current_texts = [piece]
                    current_pages = [paragraph.page]
                    current_len = len(piece)
                    flush()
                continue

            emit_text(paragraph.text, paragraph.page)

        flush()

        if not chunks:
            return ChunkingResult(
                chunks=[],
                status="empty",
                detail="No chunkable text was found in the extracted document.",
            )

        return ChunkingResult(chunks=chunks, status="completed")
