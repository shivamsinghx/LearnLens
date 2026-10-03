from __future__ import annotations

import fitz

from tests.fakes import FakeDocumentRepository


def _make_pdf_bytes(pages: list[str]) -> bytes:
    doc = fitz.open()
    try:
        for text in pages:
            page = doc.new_page()
            if text:
                page.insert_textbox(fitz.Rect(72, 72, 520, 720), text, fontsize=11)
        return doc.tobytes()
    finally:
        doc.close()


def _prepare_chunked_document(client, pages: list[str]) -> str:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("persist.pdf", _make_pdf_bytes(pages), "application/pdf"))],
    )
    document_id = upload.json()["documents"][0]["id"]
    assert client.post(f"/api/v1/documents/{document_id}/extract").status_code == 200
    assert client.post(f"/api/v1/documents/{document_id}/chunk").status_code == 200
    return document_id


def test_embed_persists_to_repository(client, fake_repository: FakeDocumentRepository):
    document_id = _prepare_chunked_document(
        client,
        ["Indexes help databases find rows quickly."],
    )

    response = client.post(f"/api/v1/documents/{document_id}/embed")
    assert response.status_code == 200
    assert response.json()["embedding_status"] == "completed"
    assert fake_repository.upsert_calls == 1
    assert fake_repository.count_chunks(document_id) >= 1
    row = fake_repository.chunks_by_document[document_id][0]
    assert row["document_id"] == document_id
    assert row["page_start"] >= 1
    assert len(row["embedding"]) == 384


def test_embed_is_idempotent_in_repository(client, fake_repository: FakeDocumentRepository):
    document_id = _prepare_chunked_document(
        client,
        ["Isolation levels protect concurrent transactions."],
    )

    first = client.post(f"/api/v1/documents/{document_id}/embed")
    second = client.post(f"/api/v1/documents/{document_id}/embed")
    assert first.status_code == second.status_code == 200
    assert fake_repository.upsert_calls == 2
    assert fake_repository.count_chunks(document_id) == first.json()["chunk_count"]
    assert len(set(fake_repository.list_chunk_ids(document_id))) == (
        fake_repository.count_chunks(document_id)
    )


def test_health_unchanged_and_ready_without_db(client, monkeypatch):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "learnlens-api"}

    monkeypatch.delenv("DATABASE_URL", raising=False)
    ready = client.get("/api/v1/ready")
    assert ready.status_code == 503
    assert "DATABASE_URL" in ready.json()["detail"]
