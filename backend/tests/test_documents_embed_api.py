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


def _upload_extract_chunk(client, filename: str, pages: list[str]) -> str:
    upload = client.post(
        "/api/v1/documents/upload",
        files=[("files", (filename, _make_pdf_bytes(pages), "application/pdf"))],
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["documents"][0]["id"]

    extract = client.post(f"/api/v1/documents/{document_id}/extract")
    assert extract.status_code == 200, extract.text
    assert extract.json()["extraction_status"] == "extracted"

    chunk = client.post(f"/api/v1/documents/{document_id}/chunk")
    assert chunk.status_code == 200, chunk.text
    assert chunk.json()["chunking_status"] == "completed"
    return document_id


def test_embed_api_success(client, upload_dir: Path):
    document_id = _upload_extract_chunk(
        client,
        "dbms.pdf",
        ["Indexes help find rows quickly.\n\nB+ trees keep ordered keys."],
    )

    response = client.post(f"/api/v1/documents/{document_id}/embed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["embedding_status"] == "completed"
    assert payload["chunk_count"] >= 1
    assert payload["embedding_dimension"] == 384
    assert payload["embedding_model"] == "fake/bge-small-en-v1.5"

    stored_path = upload_dir / f"{document_id}.embeddings.json"
    assert stored_path.is_file()
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    assert stored["embedding_dimension"] == 384
    assert len(stored["chunks"]) == payload["chunk_count"]
    first = stored["chunks"][0]
    assert first["chunk_id"].endswith("-chunk-0")
    assert len(first["embedding"]) == 384
    assert first["embedding_model"] == "fake/bge-small-en-v1.5"
    assert "Indexes" in first["text"] or "B+" in first["text"]


def test_embed_multiple_chunks(client, upload_dir: Path):
    long_page = ("Sentence about query planning and cost models. " * 40).strip()
    document_id = _upload_extract_chunk(client, "long.pdf", [long_page, long_page])

    response = client.post(f"/api/v1/documents/{document_id}/embed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunk_count"] >= 2

    stored = json.loads(
        (upload_dir / f"{document_id}.embeddings.json").read_text(encoding="utf-8")
    )
    indexes = [chunk["chunk_index"] for chunk in stored["chunks"]]
    assert indexes == list(range(len(indexes)))


def test_embed_missing_document(client):
    response = client.post(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000/embed"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_embed_missing_chunks(client):
    upload = client.post(
        "/api/v1/documents/upload",
        files=[
            (
                "files",
                (
                    "pending.pdf",
                    _make_pdf_bytes(["Text waiting for chunking."]),
                    "application/pdf",
                ),
            )
        ],
    )
    document_id = upload.json()["documents"][0]["id"]
    client.post(f"/api/v1/documents/{document_id}/extract")

    response = client.post(f"/api/v1/documents/{document_id}/embed")
    assert response.status_code == 404
    assert "chunk" in response.json()["detail"].lower()


def test_embed_empty_chunks_file(client, upload_dir: Path):
    document_id = _upload_extract_chunk(client, "ok.pdf", ["Some extractable text here."])
    # Overwrite chunks with an empty completed payload.
    (upload_dir / f"{document_id}.chunks.json").write_text(
        json.dumps(
            {
                "document_id": document_id,
                "filename": "ok.pdf",
                "chunks": [],
            }
        ),
        encoding="utf-8",
    )

    response = client.post(f"/api/v1/documents/{document_id}/embed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["embedding_status"] == "empty"
    assert payload["chunk_count"] == 0
