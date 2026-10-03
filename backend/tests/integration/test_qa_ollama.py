"""Optional live Ollama + Gemma grounded-QA checks.

Skipped automatically when Ollama or the configured model is unavailable.

Run:
  pytest -q -m llm
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.documents import DocumentMetadata, EmbeddedChunk, EmbeddedDocument
from app.models.qa import INSUFFICIENT_EVIDENCE_ANSWER
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMError, LLMService, OllamaClient
from app.services.qa_service import QAService
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from tests.fakes import FakeDocumentRepository, FakeEmbeddingBackend

pytestmark = [pytest.mark.integration, pytest.mark.llm]


@pytest.fixture(scope="module")
def live_llm():
    service = LLMService(client=OllamaClient())
    try:
        service.check_ready()
    except LLMError as exc:
        pytest.skip(f"Ollama/Gemma not available: {exc}")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Ollama/Gemma not available: {exc}")
    return service


def test_live_gemma_grounded_answer(live_llm: LLMService):
    repo = FakeDocumentRepository()
    backend = FakeEmbeddingBackend(dimension=384)
    text = (
        "Database normalization is the process of organizing data in a relational "
        "database to reduce redundancy and improve data integrity."
    )
    vector = backend.encode([text], normalize_embeddings=True)[0]
    repo.upsert_embedded_document(
        DocumentMetadata(
            id="llm-integration-doc",
            filename="DBMS Notes.pdf",
            size_bytes=1024,
            status="embedded",
            uploaded_at=datetime.now(timezone.utc),
            stored_filename="llm-integration-doc.pdf",
        ),
        EmbeddedDocument(
            document_id="llm-integration-doc",
            filename="DBMS Notes.pdf",
            embedding_model="fake/bge-small-en-v1.5",
            embedding_dimension=384,
            chunks=[
                EmbeddedChunk(
                    chunk_id="llm-integration-doc-chunk-0",
                    document_id="llm-integration-doc",
                    chunk_index=0,
                    page_start=14,
                    page_end=14,
                    text=text,
                    character_count=len(text),
                    embedding=vector,
                    embedding_model="fake/bge-small-en-v1.5",
                )
            ],
        ),
    )

    embedder = EmbeddingService(
        backend=FakeEmbeddingBackend(dimension=384),
        model_name="fake/bge-small-en-v1.5",
    )
    qa = QAService(
        retriever=RetrievalService(
            embedder=embedder,
            repository=repo,  # type: ignore[arg-type]
            config=RetrievalConfig(min_similarity=0.0, embedding_dimension=384),
        ),
        llm=live_llm,
    )

    result = qa.ask(text)
    assert result.retrieval_status == "ok"
    assert result.model == live_llm.model_name
    assert result.answer
    assert len(result.answer) > 10
    assert result.sources


def test_live_insufficient_evidence_skips_gemma(live_llm: LLMService, monkeypatch):
    repo = FakeDocumentRepository()
    embedder = EmbeddingService(
        backend=FakeEmbeddingBackend(dimension=384),
        model_name="fake/bge-small-en-v1.5",
    )
    qa = QAService(
        retriever=RetrievalService(
            embedder=embedder,
            repository=repo,  # type: ignore[arg-type]
            config=RetrievalConfig(min_similarity=0.3, embedding_dimension=384),
        ),
        llm=live_llm,
    )

    called = {"generate": False}
    original = live_llm.generate_answer

    def wrapped(*, context: str, question: str) -> str:
        called["generate"] = True
        return original(context=context, question=question)

    monkeypatch.setattr(live_llm, "generate_answer", wrapped)

    result = qa.ask("What is the capital of the underwater city of Atlantis recipes?")
    assert result.retrieval_status == "insufficient_evidence"
    assert result.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert result.model is None
    assert called["generate"] is False
