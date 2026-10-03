"""One-shot smoke: PDF → retrieve → Gemma grounded answer (requires Ollama + DB).

Usage (from backend/):
  $env:PYTHONPATH = "."
  python scripts/smoke_qa_ollama.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.api import documents as documents_api
from app.api import qa as qa_api
from app.api import retrieval as retrieval_api
from app.db.database import reset_engine
from app.main import app
from app.services.document_repository import DocumentRepository
from app.services.document_storage import DocumentStorage
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService, OllamaClient
from app.services.qa_service import QAService
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from tests.fakes import FakeEmbeddingBackend


STUDY_TEXT = (
    "Database normalization is the process of organizing data in a relational "
    "database to reduce redundancy and improve data integrity. "
    "First normal form (1NF) requires that each column hold atomic values."
)


def main() -> None:
    reset_engine()

    llm = LLMService(client=OllamaClient())
    ready = llm.check_ready()
    print("llm_ready", ready)

    tmpdir = Path(tempfile.mkdtemp(prefix="learnlens-qa-smoke-"))
    documents_api.storage = DocumentStorage(tmpdir)
    embedder = EmbeddingService(
        backend=FakeEmbeddingBackend(
            dimension=384, model_name="fake/bge-small-en-v1.5"
        ),
        model_name="fake/bge-small-en-v1.5",
    )
    documents_api.embedder = embedder
    repository = DocumentRepository(embedding_dimension=384)
    documents_api.repository = repository

    retriever = RetrievalService(
        embedder=embedder,
        repository=repository,
        config=RetrievalConfig(min_similarity=0.0, embedding_dimension=384),
    )
    retrieval_api.retriever = retriever
    qa_api.qa_service = QAService(retriever=retriever, llm=llm)

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 520, 720), STUDY_TEXT, fontsize=12)
    pdf_bytes = pdf.tobytes()
    pdf.close()

    client = TestClient(app)

    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("DBMS Notes.pdf", pdf_bytes, "application/pdf"))],
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["documents"][0]["id"]
    print("upload_ok", document_id)

    for step in ("extract", "chunk", "embed"):
        response = client.post(f"/api/v1/documents/{document_id}/{step}")
        assert response.status_code == 200, response.text
        print(step, "ok")

    supported = client.post(
        "/api/v1/qa/ask",
        json={
            "query": "What is database normalization?",
            "document_id": document_id,
            "top_k": 5,
        },
    )
    assert supported.status_code == 200, supported.text
    supported_payload = supported.json()
    print("supported", supported_payload)
    assert supported_payload["retrieval_status"] == "ok"
    assert supported_payload["model"]
    assert supported_payload["answer"]

    unsupported = client.post(
        "/api/v1/qa/ask",
        json={
            "query": "What is the capital of the underwater city of Atlantis?",
            "document_id": document_id,
            "top_k": 5,
        },
    )
    # With min_similarity=0.0 this may still retrieve something. Re-run with
    # a fresh high-threshold service for the negative path.
    high_threshold = RetrievalService(
        embedder=embedder,
        repository=repository,
        config=RetrievalConfig(min_similarity=0.99, embedding_dimension=384),
    )
    qa_api.qa_service = QAService(retriever=high_threshold, llm=llm)
    unsupported = client.post(
        "/api/v1/qa/ask",
        json={
            "query": "What is the capital of the underwater city of Atlantis?",
            "document_id": document_id,
            "top_k": 5,
        },
    )
    assert unsupported.status_code == 200, unsupported.text
    unsupported_payload = unsupported.json()
    print("unsupported", unsupported_payload)
    assert unsupported_payload["retrieval_status"] == "insufficient_evidence"
    assert unsupported_payload["model"] is None

    print("smoke_qa_ollama_ok")


if __name__ == "__main__":
    main()
