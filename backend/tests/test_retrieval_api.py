from __future__ import annotations

from datetime import datetime, timezone

from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from tests.fakes import FakeDocumentRepository, FakeEmbeddingBackend


def _seed_repo(repo: FakeDocumentRepository) -> None:
    backend = FakeEmbeddingBackend(dimension=384)
    text_a = "Database normalization reduces redundancy in relational schemas."
    text_b = "B+ trees keep leaf nodes linked for range scans."
    vectors = backend.encode([text_a, text_b], normalize_embeddings=True)
    chunks = [
        EmbeddedChunk(
            chunk_id="doc-1-chunk-0",
            document_id="doc-1",
            chunk_index=0,
            page_start=14,
            page_end=14,
            text=text_a,
            character_count=len(text_a),
            embedding=vectors[0],
            embedding_model="fake/bge-small-en-v1.5",
        ),
        EmbeddedChunk(
            chunk_id="doc-1-chunk-1",
            document_id="doc-1",
            chunk_index=1,
            page_start=20,
            page_end=21,
            text=text_b,
            character_count=len(text_b),
            embedding=vectors[1],
            embedding_model="fake/bge-small-en-v1.5",
        ),
    ]
    repo.upsert_embedded_document(
        DocumentMetadata(
            id="doc-1",
            filename="DBMS Notes.pdf",
            size_bytes=2048,
            status="embedded",
            uploaded_at=datetime.now(timezone.utc),
            stored_filename="doc-1_notes.pdf",
        ),
        EmbeddedDocument(
            document_id="doc-1",
            filename="DBMS Notes.pdf",
            embedding_model="fake/bge-small-en-v1.5",
            embedding_dimension=384,
            chunks=chunks,
        ),
    )


def test_search_api_success_and_provenance(client, fake_repository: FakeDocumentRepository):
    _seed_repo(fake_repository)
    response = client.post(
        "/api/v1/retrieval/search",
        json={"query": "Database normalization reduces redundancy in relational schemas.", "top_k": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_status"] == "ok"
    assert payload["query"].startswith("Database normalization")
    assert payload["results"]
    top = payload["results"][0]
    assert top["document_id"] == "doc-1"
    assert top["filename"] == "DBMS Notes.pdf"
    assert top["chunk_id"] == "doc-1-chunk-0"
    assert top["chunk_index"] == 0
    assert top["page_start"] == 14
    assert top["page_end"] == 14
    assert "normalization" in top["text"].lower()
    assert "similarity" in top
    assert "confidence" not in top


def test_search_api_top_k_maximum_and_empty_query(client):
    too_large = client.post(
        "/api/v1/retrieval/search",
        json={"query": "indexes", "top_k": 11},
    )
    assert too_large.status_code == 422

    empty = client.post("/api/v1/retrieval/search", json={"query": "   "})
    assert empty.status_code == 422


def test_search_api_missing_document(client, fake_repository: FakeDocumentRepository):
    response = client.post(
        "/api/v1/retrieval/search",
        json={"query": "normalization", "document_id": "missing-doc"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_search_api_document_filter(client, fake_repository: FakeDocumentRepository):
    _seed_repo(fake_repository)
    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "Database normalization reduces redundancy in relational schemas.",
            "document_id": "doc-1",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    assert all(item["document_id"] == "doc-1" for item in response.json()["results"])


def test_search_api_database_failure(client, fake_repository: FakeDocumentRepository):
    _seed_repo(fake_repository)
    fake_repository.fail_search = True
    response = client.post(
        "/api/v1/retrieval/search",
        json={"query": "Database normalization reduces redundancy in relational schemas."},
    )
    assert response.status_code == 503
