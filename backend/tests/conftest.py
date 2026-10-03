from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import documents as documents_api
from app.api import llm_ready as llm_ready_api
from app.api import qa as qa_api
from app.api import retrieval as retrieval_api
from app.main import app
from app.services.document_storage import DocumentStorage
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.qa_service import QAService
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from tests.fakes import FakeDocumentRepository, FakeEmbeddingBackend, FakeLLMClient


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    path = tmp_path / "uploads"
    path.mkdir()
    return path


@pytest.fixture
def fake_embedder() -> EmbeddingService:
    return EmbeddingService(
        backend=FakeEmbeddingBackend(),
        model_name="fake/bge-small-en-v1.5",
    )


@pytest.fixture
def fake_repository() -> FakeDocumentRepository:
    return FakeDocumentRepository()


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def client(
    upload_dir: Path,
    fake_embedder: EmbeddingService,
    fake_repository: FakeDocumentRepository,
    fake_llm_client: FakeLLMClient,
) -> TestClient:
    documents_api.storage = DocumentStorage(upload_dir)
    documents_api.embedder = fake_embedder
    documents_api.repository = fake_repository  # type: ignore[assignment]
    retriever = RetrievalService(
        embedder=fake_embedder,
        repository=fake_repository,  # type: ignore[arg-type]
        config=RetrievalConfig(
            min_similarity=0.0,  # deterministic fake vectors may score low
            embedding_dimension=384,
        ),
    )
    retrieval_api.retriever = retriever
    llm = LLMService(client=fake_llm_client)
    qa_api.qa_service = QAService(retriever=retriever, llm=llm)
    llm_ready_api.llm_service = llm
    with TestClient(app) as test_client:
        yield test_client
