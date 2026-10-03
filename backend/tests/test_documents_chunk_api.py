from __future__ import annotations

import json
from pathlib import Path

import fitz


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


def _upload_and_extract(client, filename: str, pages: list[str]) -> str:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", (filename, _make_pdf_bytes(pages), "application/pdf"))],
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["documents"][0]["id"]

    extract = client.post(f"/api/v1/documents/{document_id}/extract")
    assert extract.status_code == 200, extract.text
    return document_id


def test_chunk_endpoint_writes_chunks_json(client, upload_dir: Path):
    document_id = _upload_and_extract(
        client,
        "dbms.pdf",
        [
            "Indexes help databases find rows quickly.\n\n"
            "B+ trees keep keys sorted for range scans."
        ],
    )

    response = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["chunking_status"] == "completed"
    assert payload["chunk_count"] >= 1

    chunks_path = upload_dir / f"{document_id}.chunks.json"
    assert chunks_path.is_file()
    stored = json.loads(chunks_path.read_text(encoding="utf-8"))
    assert stored["document_id"] == document_id
    assert len(stored["chunks"]) == payload["chunk_count"]
    first = stored["chunks"][0]
    assert first["chunk_id"] == f"{document_id}-chunk-0"
    assert first["chunk_index"] == 0
    assert first["page_start"] >= 1
    assert first["page_end"] >= first["page_start"]
    assert first["character_count"] == len(first["text"])
    assert "Indexes" in first["text"] or "B+" in first["text"]


def test_chunk_multi_page_preserves_page_range(client, upload_dir: Path):
    document_id = _upload_and_extract(
        client,
        "multi.pdf",
        [
            "Page one covers transaction isolation levels in depth.",
            "Page two covers dirty reads and phantom reads carefully.",
        ],
    )

    response = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert response.status_code == 200
    stored = json.loads((upload_dir / f"{document_id}.chunks.json").read_text(encoding="utf-8"))
    pages_touched = {
        (chunk["page_start"], chunk["page_end"]) for chunk in stored["chunks"]
    }
    assert pages_touched
    assert any(start == end == 1 for start, end in pages_touched) or any(
        end >= 2 for _, end in pages_touched
    )


def test_chunk_empty_extracted_document(client, upload_dir: Path):
    document_id = _upload_and_extract(client, "blank.pdf", [""])
    response = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunking_status"] == "empty"
    assert payload["chunk_count"] == 0


def test_chunk_missing_document(client):
    response = client.post(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000/chunk"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_chunk_missing_extraction(client):
    upload = client.post(
        "/api/v1/documents/upload",
        files=[
            (
                "files",
                (
                    "pending.pdf",
                    _make_pdf_bytes(["Text waiting for extraction."]),
                    "application/pdf",
                ),
            )
        ],
    )
    document_id = upload.json()["documents"][0]["id"]
    response = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert response.status_code == 404
    assert "extraction" in response.json()["detail"].lower()


def test_chunk_invalid_extracted_json(client, upload_dir: Path):
    document_id = _upload_and_extract(client, "bad-json.pdf", ["Valid extracted text first."])
    (upload_dir / f"{document_id}.extracted.json").write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    response = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()
