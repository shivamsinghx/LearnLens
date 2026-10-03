from __future__ import annotations

from datetime import datetime, timezone

from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from app.models.qa import INSUFFICIENT_EVIDENCE_ANSWER
from app.services.llm_service import LLMError
from tests.fakes import FakeDocumentRepository, FakeEmbeddingBackend, FakeLLMClient


def _seed_repo(repo: FakeDocumentRepository) -> None:
    backend = FakeEmbeddingBackend(dimension=384)
    text = "Database normalization reduces redundancy in relational schemas."
    vector = backend.encode([text], normalize_embeddings=True)[0]
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
            chunks=[
                EmbeddedChunk(
                    chunk_id="doc-1-chunk-0",
                    document_id="doc-1",
                    chunk_index=0,
                    page_start=14,
                    page_end=15,
                    text=text,
                    character_count=len(text),
                    embedding=vector,
                    embedding_model="fake/bge-small-en-v1.5",
                )
            ],
        ),
    )


def test_ask_api_success(client, fake_repository: FakeDocumentRepository, fake_llm_client: FakeLLMClient):
    _seed_repo(fake_repository)
    response = client.post(
        "/api/v1/qa/ask",
        json={
            "query": "Database normalization reduces redundancy in relational schemas.",
            "top_k": 5,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_status"] == "ok"
    assert payload["answer"] == fake_llm_client.answer
    assert payload["model"] == "gemma3:4b"
    assert "sources" not in payload
    assert "system" not in payload
    assert len(fake_llm_client.generate_calls) == 1


def test_ask_api_insufficient_evidence_skips_llm(
    client,
    fake_repository: FakeDocumentRepository,
    fake_llm_client: FakeLLMClient,
):
    # Empty repository → no hits → insufficient evidence.
    response = client.post(
        "/api/v1/qa/ask",
        json={"query": "What is database normalization?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieval_status"] == "insufficient_evidence"
    assert payload["answer"] == INSUFFICIENT_EVIDENCE_ANSWER
    assert payload["model"] is None
    assert fake_llm_client.generate_calls == []


def test_ask_api_empty_query(client):
    response = client.post("/api/v1/qa/ask", json={"query": "   "})
    assert response.status_code == 422


def test_ask_api_ollama_unavailable(
    client,
    fake_repository: FakeDocumentRepository,
    fake_llm_client: FakeLLMClient,
):
    _seed_repo(fake_repository)
    fake_llm_client.fail_with = LLMError(
        "The language model service is unavailable.",
        status_code=503,
    )
    response = client.post(
        "/api/v1/qa/ask",
        json={
            "query": "Database normalization reduces redundancy in relational schemas.",
        },
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "The language model service is unavailable."


def test_llm_ready_endpoint(client, fake_llm_client: FakeLLMClient):
    ok = client.get("/api/v1/llm/ready")
    assert ok.status_code == 200
    assert ok.json()["status"] == "ready"
    assert ok.json()["model"] == "gemma3:4b"

    fake_llm_client.ready_ok = False
    down = client.get("/api/v1/llm/ready")
    assert down.status_code == 503


def test_health_unaffected_by_llm(client, fake_llm_client: FakeLLMClient):
    fake_llm_client.ready_ok = False
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
