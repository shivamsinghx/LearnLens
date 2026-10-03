from __future__ import annotations

from app.models.documents import ExtractedDocument, ExtractedPage
from app.services.document_chunking import ChunkingConfig, DocumentChunkingService


def _extracted(pages: list[tuple[int, str]], document_id: str = "doc-1") -> ExtractedDocument:
    return ExtractedDocument(
        document_id=document_id,
        filename="notes.pdf",
        pages=[ExtractedPage(page_number=page, text=text) for page, text in pages],
    )


def test_basic_paragraph_chunking_combines_small_paragraphs():
    service = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=80, max_chunk_size=120, overlap=10)
    )
    extracted = _extracted(
        [
            (
                1,
                "First paragraph about indexes.\n\n"
                "Second paragraph about joins.\n\n"
                "Third paragraph about keys.",
            )
        ]
    )

    result = service.chunk_extracted(extracted)
    assert result.status == "completed"
    assert result.chunks
    assert result.chunks[0].chunk_index == 0
    assert result.chunks[0].document_id == "doc-1"
    assert "First paragraph" in result.chunks[0].text
    assert "Second paragraph" in result.chunks[0].text


def test_multiple_paragraphs_and_ordering():
    service = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=40, max_chunk_size=60, overlap=5)
    )
    long_a = "A" * 45
    long_b = "B" * 45
    extracted = _extracted([(1, f"{long_a}\n\n{long_b}")])

    result = service.chunk_extracted(extracted)
    assert result.status == "completed"
    assert len(result.chunks) >= 2
    assert [chunk.chunk_index for chunk in result.chunks] == list(
        range(len(result.chunks))
    )
    assert [chunk.chunk_id for chunk in result.chunks] == [
        f"doc-1-chunk-{index}" for index in range(len(result.chunks))
    ]


def test_long_paragraph_splitting_and_overlap():
    service = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=50, max_chunk_size=60, overlap=12)
    )
    sentence = "This is a sentence about database storage engines. "
    text = sentence * 8
    extracted = _extracted([(1, text)])

    result = service.chunk_extracted(extracted)
    assert result.status == "completed"
    assert len(result.chunks) >= 2

    # Overlap: later chunk should reuse trailing content from the prior chunk.
    first = result.chunks[0].text
    second = result.chunks[1].text
    assert any(token in second for token in first.split()[-3:])


def test_page_metadata_single_and_multi_page():
    service = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=200, max_chunk_size=300, overlap=20)
    )
    extracted = _extracted(
        [
            (1, "Page one introduces B+ trees and leaf nodes in detail."),
            (2, "Page two continues with internal nodes and fanout."),
            (3, ""),
        ]
    )

    result = service.chunk_extracted(extracted)
    assert result.status == "completed"
    assert result.chunks[0].page_start == 1
    assert result.chunks[0].page_end >= 1

    # Force a multi-page chunk by using a large target.
    wide = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=1000, max_chunk_size=1500, overlap=50)
    )
    wide_result = wide.chunk_extracted(extracted)
    assert wide_result.chunks[0].page_start == 1
    assert wide_result.chunks[0].page_end == 2


def test_empty_pages_and_empty_document():
    service = DocumentChunkingService()
    empty_pages = service.chunk_extracted(_extracted([(1, ""), (2, "   "), (3, "\n\n")]))
    assert empty_pages.status == "empty"
    assert empty_pages.chunks == []

    no_pages = service.chunk_extracted(
        ExtractedDocument(document_id="doc-1", filename="notes.pdf", pages=[])
    )
    assert no_pages.status == "empty"
    assert no_pages.chunks == []


def test_one_page_document_and_small_chunks():
    service = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=1200, max_chunk_size=1500, overlap=200)
    )
    extracted = _extracted([(1, "Only a short note about SQL joins.")])
    result = service.chunk_extracted(extracted)
    assert result.status == "completed"
    assert len(result.chunks) == 1
    assert result.chunks[0].page_start == result.chunks[0].page_end == 1
    assert result.chunks[0].character_count == len(result.chunks[0].text)


def test_configurable_chunk_size_and_overlap():
    text = ("Sentence about query optimization stays informative. " * 40).strip()
    extracted = _extracted([(1, text)])

    small = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=120, max_chunk_size=160, overlap=20)
    ).chunk_extracted(extracted)
    large = DocumentChunkingService(
        ChunkingConfig(target_chunk_size=800, max_chunk_size=1000, overlap=50)
    ).chunk_extracted(extracted)

    assert small.status == large.status == "completed"
    assert len(small.chunks) > len(large.chunks)
