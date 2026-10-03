from __future__ import annotations

import math

from app.models.documents import DocumentChunk
from app.services.embedding_service import EmbeddingService, get_embedding_model_name
from tests.fakes import FakeEmbeddingBackend


def _chunk(text: str, index: int = 0) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"doc-chunk-{index}",
        document_id="doc-1",
        chunk_index=index,
        page_start=1,
        page_end=1,
        text=text,
        character_count=len(text),
    )


def test_default_model_name_from_env(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert get_embedding_model_name() == "BAAI/bge-small-en-v1.5"

    monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    assert get_embedding_model_name() == "sentence-transformers/all-MiniLM-L6-v2"


def test_successful_single_and_batch_embedding():
    service = EmbeddingService(backend=FakeEmbeddingBackend(dimension=384))

    single = service.embed_text("Indexes speed up lookups.")
    assert len(single) == 384
    assert math.isclose(math.sqrt(sum(v * v for v in single)), 1.0, rel_tol=1e-6)

    batch = service.embed_texts(
        ["Indexes speed up lookups.", "Joins combine related tables."]
    )
    assert len(batch) == 2
    assert all(len(vector) == 384 for vector in batch)
    assert batch[0] == single
    assert batch[0] != batch[1]


def test_embedding_is_repeatable_for_same_input():
    service = EmbeddingService(backend=FakeEmbeddingBackend())
    first = service.embed_text("B+ trees keep keys ordered.")
    second = service.embed_text("B+ trees keep keys ordered.")
    assert first == second


def test_embed_chunks_attaches_metadata():
    service = EmbeddingService(
        backend=FakeEmbeddingBackend(model_name="fake/bge-small-en-v1.5")
    )
    chunks = [
        _chunk("First chunk about transactions.", 0),
        _chunk("Second chunk about isolation.", 1),
    ]

    result = service.embed_chunks(chunks)
    assert result.status == "completed"
    assert result.embedding_dimension == 384
    assert result.embedding_model == "fake/bge-small-en-v1.5"
    assert len(result.chunks) == 2

    first = result.chunks[0]
    assert first.chunk_id == "doc-chunk-0"
    assert first.document_id == "doc-1"
    assert first.chunk_index == 0
    assert first.page_start == 1
    assert first.page_end == 1
    assert first.embedding_model == "fake/bge-small-en-v1.5"
    assert len(first.embedding) == 384
    assert first.text.startswith("First chunk")


def test_empty_chunk_list():
    service = EmbeddingService(backend=FakeEmbeddingBackend())
    result = service.embed_chunks([])
    assert result.status == "empty"
    assert result.chunks == []
    assert result.embedding_dimension == 384


def test_normalization_can_be_disabled():
    backend = FakeEmbeddingBackend(dimension=8)
    service = EmbeddingService(backend=backend)
    raw = service.embed_text("raw vector", normalize=False)
    norm = math.sqrt(sum(v * v for v in raw))
    assert not math.isclose(norm, 1.0, rel_tol=1e-3)
