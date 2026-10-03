"""Build structured prompt context from semantic retrieval hits.

Only retrieved chunks are included — never the full PDF.
Retrieved document text is treated as untrusted content and must be
clearly delimited from system instructions.
"""

from __future__ import annotations

from app.models.retrieval import RetrievalResult

# Delimiters keep study-material text from being interpreted as instructions.
CONTEXT_BEGIN = "<<<STUDY_MATERIAL_CONTEXT>>>"
CONTEXT_END = "<<<END_STUDY_MATERIAL_CONTEXT>>>"


def format_page_range(page_start: int, page_end: int) -> str:
    if page_start == page_end:
        return str(page_start)
    return f"{page_start}-{page_end}"


def build_source_block(index: int, result: RetrievalResult) -> str:
    pages = format_page_range(result.page_start, result.page_end)
    return (
        f"SOURCE {index}\n"
        f"Document: {result.filename}\n"
        f"Pages: {pages}\n"
        f"\n"
        f"{result.text.strip()}"
    )


def build_context(results: list[RetrievalResult]) -> str:
    """Transform retrieval results into delimited prompt context."""
    if not results:
        return f"{CONTEXT_BEGIN}\n(no retrieved sources)\n{CONTEXT_END}"

    blocks = [
        build_source_block(index, result)
        for index, result in enumerate(results, start=1)
    ]
    body = "\n\n".join(blocks)
    return f"{CONTEXT_BEGIN}\n{body}\n{CONTEXT_END}"
