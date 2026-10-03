from __future__ import annotations

from app.models.retrieval import RetrievalResult
from app.services.context_builder import CONTEXT_BEGIN, CONTEXT_END, build_context


def test_build_context_includes_metadata_and_delimiters():
    results = [
        RetrievalResult(
            chunk_id="c1",
            document_id="d1",
            filename="DBMS Notes.pdf",
            chunk_index=0,
            page_start=14,
            page_end=15,
            text="Normalization reduces redundancy.",
            similarity=0.9,
        ),
        RetrievalResult(
            chunk_id="c2",
            document_id="d1",
            filename="DBMS Notes.pdf",
            chunk_index=1,
            page_start=17,
            page_end=17,
            text="1NF requires atomic values.",
            similarity=0.8,
        ),
    ]
    context = build_context(results)
    assert CONTEXT_BEGIN in context
    assert CONTEXT_END in context
    assert "SOURCE 1" in context
    assert "SOURCE 2" in context
    assert "Document: DBMS Notes.pdf" in context
    assert "Pages: 14-15" in context
    assert "Pages: 17" in context
    assert "Normalization reduces redundancy." in context
    assert "1NF requires atomic values." in context
