from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Sequence

import pytest

from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalConfig, RetrievalError, RetrievalService
from tests.fakes import FakeDocumentRepository


class FixedEmbeddingBackend:
    def __init__(self, mapping: dict[str, list[float]], *, dimension: int = 4) -> None:
        self.mapping = mapping
        self._dimension = dimension
        self._model_name = "fixed-test-model"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool = True,
    ) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = list(self.mapping[text])
            if normalize_embeddings:
                norm = math.sqrt(sum(v * v for v in vector))
                vector = [v / norm for v in vector]
            vectors.append(vector)
        return vectors


def _meta(document_id: str, filename: str = "DBMS Notes.pdf") -> DocumentMetadata:
    return DocumentMetadata(
        id=document_id,
        filename=filename,
        size_bytes=100,
        status="embedded",
        uploaded_at=datetime.now(timezone.utc),
        stored_filename=f"{document_id}.pdf",
    )


def _seed(
    repo: FakeDocumentRepository,
    document_id: str,
    chunks: list[tuple[str, list[float], int, int]],
    filename: str = "DBMS Notes.pdf",
) -> None:
    embedded_chunks = [
        EmbeddedChunk(
            chunk_id=f"{document_id}-chunk-{index}",
            document_id=document_id,
            chunk_index=index,
            page_start=page_start,
            page_end=page_end,
            text=text,
            character_count=len(text),
            embedding=vector,
            embedding_model="fixed-test-model",
        )
        for index, (text, vector, page_start, page_end) in enumerate(chunks)
    ]
    repo.upsert_embedded_document(
        _meta(document_id, filename),
        EmbeddedDocument(
            document_id=document_id,
            filename=filename,
            embedding_model="fixed-test-model",
            embedding_dimension=4,
            chunks=embedded_chunks,
        ),
    )


def test_successful_retrieval_ordering_and_provenance():
    repo = FakeDocumentRepository(embedding_dimension=4)
    _seed(
        repo,
        "doc-a",
        [
            ("Normalization organizes tables to reduce redundancy.", [1.0, 0.0, 0.0, 0.0], 14, 15),
            ("Indexes speed up lookups on large tables.", [0.0, 1.0, 0.0, 0.0], 3, 3),
        ],
    )
    embedder = EmbeddingService(
        backend=FixedEmbeddingBackend(
            {"What is database normalization?": [1.0, 0.1, 0.0, 0.0]},
            dimension=4,
        ),
        model_name="fixed-test-model",
    )
    service = RetrievalService(
        embedder=embedder,
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(min_similarity=0.0, embedding_dimension=4),
    )

    response = service.search("What is database normalization?", top_k=5)
    assert response.retrieval_status == "ok"
    assert len(response.results) == 2
    assert response.results[0].similarity >= response.results[1].similarity
    top = response.results[0]
    assert top.document_id == "doc-a"
    assert top.filename == "DBMS Notes.pdf"
    assert top.chunk_id.endswith("-chunk-0")
    assert top.chunk_index == 0
    assert top.page_start == 14
    assert top.page_end == 15
    assert "Normalization" in top.text


def test_top_k_limit_and_maximum():
    repo = FakeDocumentRepository(embedding_dimension=4)
    chunks = [
        (f"chunk {index}", [1.0, float(index) * 0.01, 0.0, 0.0], 1, 1)
        for index in range(8)
    ]
    _seed(repo, "doc-a", chunks)
    embedder = EmbeddingService(
        backend=FixedEmbeddingBackend(
            {"query": [1.0, 0.0, 0.0, 0.0]},
            dimension=4,
        )
    )
    service = RetrievalService(
        embedder=embedder,
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(min_similarity=0.0, max_top_k=10, embedding_dimension=4),
    )
    assert len(service.search("query", top_k=3).results) == 3
    with pytest.raises(RetrievalError, match="top_k"):
        service.search("query", top_k=11)


def test_document_filter_and_global_search():
    repo = FakeDocumentRepository(embedding_dimension=4)
    _seed(repo, "doc-a", [("Alpha normalization text", [1.0, 0.0, 0.0, 0.0], 1, 1)], "A.pdf")
    _seed(repo, "doc-b", [("Beta normalization text", [0.9, 0.1, 0.0, 0.0], 2, 2)], "B.pdf")
    embedder = EmbeddingService(
        backend=FixedEmbeddingBackend(
            {"normalization": [1.0, 0.0, 0.0, 0.0]},
            dimension=4,
        )
    )
    service = RetrievalService(
        embedder=embedder,
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(min_similarity=0.0, embedding_dimension=4),
    )

    scoped = service.search("normalization", document_id="doc-a", top_k=5)
    assert scoped.retrieval_status == "ok"
    assert all(item.document_id == "doc-a" for item in scoped.results)

    global_hits = service.search("normalization", top_k=5)
    assert {item.document_id for item in global_hits.results} == {"doc-a", "doc-b"}


def test_similarity_threshold_insufficient_evidence():
    repo = FakeDocumentRepository(embedding_dimension=4)
    _seed(repo, "doc-a", [("unrelated topic about cooking", [0.0, 1.0, 0.0, 0.0], 1, 1)])
    embedder = EmbeddingService(
        backend=FixedEmbeddingBackend(
            {"What is database normalization?": [1.0, 0.0, 0.0, 0.0]},
            dimension=4,
        )
    )
    service = RetrievalService(
        embedder=embedder,
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(min_similarity=0.8, embedding_dimension=4),
    )
    response = service.search("What is database normalization?")
    assert response.retrieval_status == "insufficient_evidence"
    assert response.results == []


def test_empty_query_and_missing_document():
    repo = FakeDocumentRepository(embedding_dimension=4)
    service = RetrievalService(
        embedder=EmbeddingService(
            backend=FixedEmbeddingBackend({"x": [1.0, 0.0, 0.0, 0.0]}, dimension=4)
        ),
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(embedding_dimension=4),
    )
    with pytest.raises(RetrievalError) as empty:
        service.search("   ")
    assert empty.value.status_code == 422

    with pytest.raises(RetrievalError) as missing:
        service.search("x", document_id="missing")
    assert missing.value.status_code == 404


def test_document_with_no_chunks():
    repo = FakeDocumentRepository(embedding_dimension=4)
    repo.documents["empty-doc"] = _meta("empty-doc")
    repo.filenames["empty-doc"] = "empty.pdf"
    service = RetrievalService(
        embedder=EmbeddingService(
            backend=FixedEmbeddingBackend({"q": [1.0, 0.0, 0.0, 0.0]}, dimension=4)
        ),
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(embedding_dimension=4),
    )
    response = service.search("q", document_id="empty-doc")
    assert response.retrieval_status == "insufficient_evidence"
    assert response.results == []


def test_database_failure_and_query_embedding_dimension():
    repo = FakeDocumentRepository(embedding_dimension=4, fail_search=True)
    _seed(repo, "doc-a", [("text", [1.0, 0.0, 0.0, 0.0], 1, 1)])
    service = RetrievalService(
        embedder=EmbeddingService(
            backend=FixedEmbeddingBackend({"q": [1.0, 0.0, 0.0, 0.0]}, dimension=4)
        ),
        repository=repo,  # type: ignore[arg-type]
        config=RetrievalConfig(min_similarity=0.0, embedding_dimension=4),
    )
    with pytest.raises(RetrievalError) as exc:
        service.search("q")
    assert exc.value.status_code == 503

    # Normalized query embedding length must match configured dimension.
    vector = service.embedder.embed_text("q", normalize=True)
    assert len(vector) == 4
    assert math.isclose(math.sqrt(sum(v * v for v in vector)), 1.0, rel_tol=1e-6)
