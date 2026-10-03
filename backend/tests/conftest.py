from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import documents as documents_api
from app.main import app
from app.services.document_storage import DocumentStorage


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    path = tmp_path / "uploads"
    path.mkdir()
    return path


@pytest.fixture
def client(upload_dir: Path) -> TestClient:
    documents_api.storage = DocumentStorage(upload_dir)
    with TestClient(app) as test_client:
        yield test_client
