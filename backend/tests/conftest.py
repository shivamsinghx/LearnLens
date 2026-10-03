from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import documents as documents_api
from app.api import retrieval as retrieval_api
from app.main import app
from app.services.document_storage import DocumentStorage
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalConfig, RetrievalService
from tests.fakes import FakeDocumentRepository, FakeEmbeddingBackend


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
def client(
    upload_dir: Path,
    fake_embedder: EmbeddingService,
    fake_repository: FakeDocumentRepository,
) -> TestClient:
    documents_api.storage = DocumentStorage(upload_dir)
    documents_api.embedder = fake_embedder
    documents_api.repository = fake_repository  # type: ignore[assignment]
    retrieval_api.retriever = RetrievalService(
        embedder=fake_embedder,
        repository=fake_repository,  # type: ignore[arg-type]
        config=RetrievalConfig(
            min_similarity=0.0,  # deterministic fake vectors may score low
            embedding_dimension=384,
        ),
    )
    with TestClient(app) as test_client:
        yield test_client
