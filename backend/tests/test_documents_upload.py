from __future__ import annotations

from pathlib import Path

from app.utils.pdf import MAX_FILE_BYTES, MAX_FILES_PER_BATCH


def _pdf_bytes(extra: bytes = b"") -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + extra


def test_upload_single_pdf_returns_metadata(client, upload_dir: Path):
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("notes.pdf", _pdf_bytes(), "application/pdf"))],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["errors"] == []
    assert len(payload["documents"]) == 1

    document = payload["documents"][0]
    assert document["filename"] == "notes.pdf"
    assert document["status"] == "uploaded"
    assert document["size_bytes"] == len(_pdf_bytes())
    assert document["id"]
    assert document["uploaded_at"]
    assert document["stored_filename"].startswith(f"{document['id']}_")

    stored = upload_dir / document["stored_filename"]
    assert stored.is_file()
    assert stored.read_bytes().startswith(b"%PDF")
    assert (upload_dir / f"{document['id']}.json").is_file()


def test_upload_multiple_pdfs(client):
    files = [
        ("files", ("a.pdf", _pdf_bytes(b"a"), "application/pdf")),
        ("files", ("b.pdf", _pdf_bytes(b"b"), "application/pdf")),
    ]
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    assert len(response.json()["documents"]) == 2


def test_reject_non_pdf_extension(client):
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("notes.txt", _pdf_bytes(), "text/plain"))],
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_reject_invalid_pdf_magic(client):
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("fake.pdf", b"not-a-pdf", "application/pdf"))],
    )
    assert response.status_code == 400


def test_reject_oversized_file(client):
    huge = _pdf_bytes(b"x" * (MAX_FILE_BYTES + 1))
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("huge.pdf", huge, "application/pdf"))],
    )
    assert response.status_code == 400
    assert "size limit" in response.json()["detail"].lower()


def test_reject_too_many_files(client):
    files = [
        ("files", (f"{index}.pdf", _pdf_bytes(bytes([index])), "application/pdf"))
        for index in range(MAX_FILES_PER_BATCH + 1)
    ]
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert str(MAX_FILES_PER_BATCH) in response.json()["detail"]


def test_partial_success_keeps_valid_files(client):
    files = [
        ("files", ("good.pdf", _pdf_bytes(), "application/pdf")),
        ("files", ("bad.txt", b"hello", "text/plain")),
    ]
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    payload = response.json()
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["filename"] == "good.pdf"
    assert len(payload["errors"]) == 1
    assert payload["errors"][0]["filename"] == "bad.txt"


def test_sanitize_path_traversal_filename(client, upload_dir: Path):
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("../../evil.pdf", _pdf_bytes(), "application/pdf"))],
    )
    assert response.status_code == 201
    stored_name = response.json()["documents"][0]["stored_filename"]
    assert ".." not in stored_name
    assert (upload_dir / stored_name).is_file()
    assert list(upload_dir.glob("*.pdf"))  # stayed inside upload_dir
