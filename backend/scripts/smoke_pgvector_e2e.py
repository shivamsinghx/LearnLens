"""One-shot local smoke: upload → extract → chunk → embed → PostgreSQL."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.api import documents as documents_api
from app.db.database import reset_engine, session_scope
from app.db.models import DocumentChunkRow, DocumentRow
from app.main import app
from app.services.document_repository import DocumentRepository
from app.services.document_storage import DocumentStorage
from app.services.embedding_service import EmbeddingService
from tests.fakes import FakeEmbeddingBackend


def main() -> None:
    reset_engine()

    tmpdir = Path(tempfile.mkdtemp(prefix="learnlens-smoke-"))
    documents_api.storage = DocumentStorage(tmpdir)
    # Deterministic 384-d vectors (no model download) while hitting real PostgreSQL.
    documents_api.embedder = EmbeddingService(
        backend=FakeEmbeddingBackend(
            dimension=384, model_name="fake/bge-small-en-v1.5"
        ),
        model_name="fake/bge-small-en-v1.5",
    )
    documents_api.repository = DocumentRepository(embedding_dimension=384)

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(
        fitz.Rect(72, 72, 520, 720),
        "LearnLens smoke test notes about B+ trees and indexes.\n\n"
        "Secondary paragraph covers page provenance for citations.",
        fontsize=12,
    )
    pdf_bytes = pdf.tobytes()
    pdf.close()

    client = TestClient(app)

    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("smoke-notes.pdf", pdf_bytes, "application/pdf"))],
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["documents"][0]["id"]
    print("upload_ok", document_id)

    extract = client.post(f"/api/v1/documents/{document_id}/extract")
    assert extract.status_code == 200, extract.text
    print(
        "extract",
        extract.json()["extraction_status"],
        "pages",
        extract.json()["page_count"],
    )

    chunk = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert chunk.status_code == 200, chunk.text
    print(
        "chunk",
        chunk.json()["chunking_status"],
        "count",
        chunk.json()["chunk_count"],
    )

    embed = client.post(f"/api/v1/documents/{document_id}/embed")
    assert embed.status_code == 200, embed.text
    print("embed", embed.json())

    with session_scope() as session:
        document = session.get(DocumentRow, document_id)
        assert document is not None, "document row missing"
        rows = list(
            session.scalars(
                select(DocumentChunkRow).where(
                    DocumentChunkRow.document_id == document_id
                )
            )
        )
        assert rows, "expected persisted chunks"
        for row in rows:
            dim = session.execute(
                text("SELECT vector_dims(embedding) FROM document_chunks WHERE id = :id"),
                {"id": row.id},
            ).scalar_one()
            print(
                "chunk_row",
                row.id,
                "index",
                row.chunk_index,
                "pages",
                f"{row.page_start}-{row.page_end}",
                "dims",
                dim,
                "model",
                row.embedding_model,
                "text_preview",
                row.text[:48].replace("\n", " "),
            )
            assert dim == 384
            assert len(list(row.embedding)) == 384

    print("E2E_PERSIST_OK", "chunks", len(rows))


if __name__ == "__main__":
    main()
