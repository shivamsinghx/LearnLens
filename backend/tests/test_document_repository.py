from __future__ import annotations

from datetime import datetime, timezone

from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from tests.fakes import FakeDocumentRepository


def _metadata(document_id: str = "doc-1") -> DocumentMetadata:
    return DocumentMetadata(
        id=document_id,
        filename="notes.pdf",
        size_bytes=1234,
        status="embedded",
        uploaded_at=datetime.now(timezone.utc),
        stored_filename=f"{document_id}_notes.pdf",
        embedding_status="completed",
        embedding_model="fake/bge-small-en-v1.5",
        embedding_dimension=384,
    )


def _embedded(document_id: str, texts: list[str]) -> EmbeddedDocument:
    chunks = [
        EmbeddedChunk(
            chunk_id=f"{document_id}-chunk-{index}",
            document_id=document_id,
            chunk_index=index,
            page_start=index + 1,
            page_end=index + 1,
            text=text,
            character_count=len(text),
            embedding=[0.0] * 383 + [1.0],
            embedding_model="fake/bge-small-en-v1.5",
        )
        for index, text in enumerate(texts)
    ]
    return EmbeddedDocument(
        document_id=document_id,
        filename="notes.pdf",
        embedding_model="fake/bge-small-en-v1.5",
        embedding_dimension=384,
        chunks=chunks,
    )


def test_document_and_chunk_insertion_with_vector_dimension():
    repo = FakeDocumentRepository()
    embedded = _embedded("doc-1", ["chunk a", "chunk b"])
    repo.upsert_embedded_document(_metadata(), embedded)

    assert "doc-1" in repo.documents
    assert repo.count_chunks("doc-1") == 2
    rows = repo.chunks_by_document["doc-1"]
    assert rows[0]["page_start"] == 1
    assert rows[1]["page_end"] == 2
    assert len(rows[0]["embedding"]) == 384
    assert rows[0]["embedding_model"] == "fake/bge-small-en-v1.5"


def test_idempotent_upsert_replaces_chunks():
    repo = FakeDocumentRepository()
    meta = _metadata()
    repo.upsert_embedded_document(meta, _embedded("doc-1", ["one", "two", "three"]))
    assert repo.count_chunks("doc-1") == 3

    repo.upsert_embedded_document(meta, _embedded("doc-1", ["only-one"]))
    assert repo.upsert_calls == 2
    assert repo.count_chunks("doc-1") == 1
    assert repo.list_chunk_ids("doc-1") == ["doc-1-chunk-0"]


def test_cascade_delete_removes_chunks():
    repo = FakeDocumentRepository()
    repo.upsert_embedded_document(_metadata(), _embedded("doc-1", ["a", "b"]))
    repo.delete_document("doc-1")
    assert repo.count_chunks("doc-1") == 0
    assert "doc-1" not in repo.documents


def test_dimension_mismatch_rejected():
    repo = FakeDocumentRepository(embedding_dimension=384)
    bad = EmbeddedChunk(
        chunk_id="doc-1-chunk-0",
        document_id="doc-1",
        chunk_index=0,
        page_start=1,
        page_end=1,
        text="bad",
        character_count=3,
        embedding=[0.1, 0.2],
        embedding_model="fake/bge-small-en-v1.5",
    )
    embedded = EmbeddedDocument(
        document_id="doc-1",
        filename="notes.pdf",
        embedding_model="fake/bge-small-en-v1.5",
        embedding_dimension=384,
        chunks=[bad],
    )
    try:
        repo.upsert_embedded_document(_metadata(), embedded)
        raised = False
    except ValueError:
        raised = True
    assert raised
