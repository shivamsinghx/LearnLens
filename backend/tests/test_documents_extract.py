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
                rect = fitz.Rect(72, 72, 520, 720)
                page.insert_textbox(rect, text, fontsize=12)
        return doc.tobytes()
    finally:
        doc.close()


def _upload_pdf(client, filename: str, content: bytes) -> str:
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", (filename, content, "application/pdf"))],
    )
    assert response.status_code == 201, response.text
    return response.json()["documents"][0]["id"]


def test_extract_successful_text(client, upload_dir: Path):
    document_id = _upload_pdf(
        client,
        "dbms-notes.pdf",
        _make_pdf_bytes(["Relational databases store tables and relations."]),
    )

    response = client.post(f"/api/v1/documents/{document_id}/extract")
    assert response.status_code == 200
    payload = response.json()

    assert payload["document_id"] == document_id
    assert payload["filename"] == "dbms-notes.pdf"
    assert payload["page_count"] == 1
    assert payload["extraction_status"] == "extracted"
    assert payload["detail"] is None
    assert len(payload["pages"]) == 1
    assert payload["pages"][0]["page_number"] == 1
    assert "Relational databases" in payload["pages"][0]["text"]

    stored = upload_dir / f"{document_id}.extracted.json"
    assert stored.is_file()
    assert "Relational databases" in stored.read_text(encoding="utf-8")


def test_extract_multi_page_preserves_page_numbers(client):
    document_id = _upload_pdf(
        client,
        "multi.pdf",
        _make_pdf_bytes(
            [
                "Page one introduces indexes.",
                "Page two covers B+ trees.",
                "Page three discusses query planning.",
            ]
        ),
    )

    response = client.post(f"/api/v1/documents/{document_id}/extract")
    assert response.status_code == 200
    payload = response.json()

    assert payload["extraction_status"] == "extracted"
    assert payload["page_count"] == 3
    assert [page["page_number"] for page in payload["pages"]] == [1, 2, 3]
    assert "indexes" in payload["pages"][0]["text"]
    assert "B+ trees" in payload["pages"][1]["text"]
    assert "query planning" in payload["pages"][2]["text"]


def test_extract_normalizes_whitespace(client):
    document_id = _upload_pdf(
        client,
        "spacing.pdf",
        _make_pdf_bytes(["Hello    world\n\n\n\nNext     line"]),
    )

    response = client.post(f"/api/v1/documents/{document_id}/extract")
    assert response.status_code == 200
    text = response.json()["pages"][0]["text"]

    assert "Hello    world" not in text
    assert "Hello world" in text
    assert "\n\n\n" not in text
    assert "Next line" in text


def test_extract_empty_scanned_pdf_detected(client):
    document_id = _upload_pdf(client, "blank.pdf", _make_pdf_bytes([""]))

    response = client.post(f"/api/v1/documents/{document_id}/extract")
    assert response.status_code == 200
    payload = response.json()

    assert payload["extraction_status"] == "empty"
    assert payload["page_count"] == 1
    assert payload["pages"][0]["page_number"] == 1
    assert payload["pages"][0]["text"] == ""
    assert payload["detail"]
    assert "meaningful" in payload["detail"].lower() or "scanned" in payload["detail"].lower()


def test_extract_missing_document(client):
    response = client.post(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000/extract"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_extract_corrupted_pdf(client, upload_dir: Path):
    # Upload stores any payload with PDF magic; overwrite with corrupted bytes.
    document_id = _upload_pdf(
        client,
        "corrupt.pdf",
        b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n",
    )
    metadata = json.loads((upload_dir / f"{document_id}.json").read_text(encoding="utf-8"))
    (upload_dir / metadata["stored_filename"]).write_bytes(
        b"%PDF-1.4 corrupted-not-a-real-pdf"
    )

    response = client.post(f"/api/v1/documents/{document_id}/extract")
    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_status"] == "failed"
    assert payload["detail"]
    assert payload["pages"] == []
