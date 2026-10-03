"""Live PostgreSQL + pgvector retrieval check.

Skipped automatically when the database is unreachable.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.db.database import check_database_ready, reset_engine
from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from app.services.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from tests.fakes import FakeEmbeddingBackend

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_db():
    reset_engine()
    try:
        check_database_ready()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL + pgvector not available: {exc}")
    yield
    reset_engine()


def test_live_pgvector_cosine_search(live_db):
    document_id = "integration-retrieval-doc"
    repo = DocumentRepository(embedding_dimension=384)
    embedder = EmbeddingService(
        backend=FakeEmbeddingBackend(dimension=384),
        model_name="fake/bge-small-en-v1.5",
    )

    relevant = "Database normalization organizes tables to reduce redundancy."
    distractor = "Cooking pasta requires salted boiling water."
    relevant_vector = embedder.embed_text(relevant, normalize=True)
    distractor_vector = embedder.embed_text(distractor, normalize=True)

    repo.upsert_embedded_document(
        DocumentMetadata(
            id=document_id,
            filename="DBMS Notes.pdf",
            size_bytes=1024,
            status="embedded",
            uploaded_at=datetime.now(timezone.utc),
            stored_filename=f"{document_id}.pdf",
        ),
        EmbeddedDocument(
            document_id=document_id,
            filename="DBMS Notes.pdf",
            embedding_model="fake/bge-small-en-v1.5",
            embedding_dimension=384,
            chunks=[
                EmbeddedChunk(
                    chunk_id=f"{document_id}-chunk-0",
                    document_id=document_id,
                    chunk_index=0,
                    page_start=14,
                    page_end=14,
                    text=relevant,
                    character_count=len(relevant),
                    embedding=relevant_vector,
                    embedding_model="fake/bge-small-en-v1.5",
                ),
                EmbeddedChunk(
                    chunk_id=f"{document_id}-chunk-1",
                    document_id=document_id,
                    chunk_index=1,
                    page_start=2,
                    page_end=2,
                    text=distractor,
                    character_count=len(distractor),
                    embedding=distractor_vector,
                    embedding_model="fake/bge-small-en-v1.5",
                ),
            ],
        ),
    )

    service = RetrievalService(
        embedder=embedder,
        repository=repo,
        config=RetrievalConfig(min_similarity=0.2, embedding_dimension=384),
    )
    response = service.search(relevant, document_id=document_id, top_k=5)

    assert response.retrieval_status == "ok"
    assert response.results
    assert response.results[0].chunk_id == f"{document_id}-chunk-0"
    assert response.results[0].page_start == 14
    assert response.results[0].filename == "DBMS Notes.pdf"
    assert response.results[0].similarity >= response.results[-1].similarity

    repo.delete_document(document_id)
