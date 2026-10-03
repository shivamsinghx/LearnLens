"""Semantic retrieval over pgvector-stored chunk embeddings.

Pipeline stage:
  question → embed (same model as chunks) → cosine search in PostgreSQL → evidence
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.settings import get_embedding_dimension, get_retrieval_min_similarity
from app.models.retrieval import (
    DEFAULT_TOP_K,
    MAX_TOP_K,
    RetrievalResult,
    RetrievalSearchResponse,
)
from app.services.document_repository import DocumentRepository, SimilarChunkHit
from app.services.embedding_service import EmbeddingService


class RetrievalError(Exception):
    """Domain error for retrieval failures that map to HTTP responses."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class RetrievalConfig:
    min_similarity: float = 0.3
    default_top_k: int = DEFAULT_TOP_K
    max_top_k: int = MAX_TOP_K
    embedding_dimension: int = 384


class RetrievalService:
    """Embed a question and retrieve the most similar document chunks."""

    def __init__(
        self,
        *,
        embedder: EmbeddingService | None = None,
        repository: DocumentRepository | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.embedder = embedder or EmbeddingService()
        self.repository = repository or DocumentRepository()
        self.config = config or RetrievalConfig(
            min_similarity=get_retrieval_min_similarity(),
            embedding_dimension=get_embedding_dimension(),
        )

    def search(
        self,
        query: str,
        *,
        document_id: str | None = None,
        top_k: int | None = None,
    ) -> RetrievalSearchResponse:
        cleaned = (query or "").strip()
        if not cleaned:
            raise RetrievalError("query must not be empty.", status_code=422)

        limit = top_k if top_k is not None else self.config.default_top_k
        if limit < 1:
            raise RetrievalError("top_k must be >= 1.", status_code=422)
        if limit > self.config.max_top_k:
            raise RetrievalError(
                f"top_k cannot exceed {self.config.max_top_k}.",
                status_code=422,
            )

        if document_id is not None:
            if not self.repository.document_exists(document_id):
                raise RetrievalError("Document not found.", status_code=404)
            if self.repository.count_chunks(document_id) == 0:
                return RetrievalSearchResponse(
                    query=cleaned,
                    results=[],
                    retrieval_status="insufficient_evidence",
                    detail="This document has no embedded chunks to search.",
                )

        try:
            query_vector = self.embedder.embed_text(cleaned, normalize=True)
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(
                "Embedding model is unavailable.",
                status_code=503,
            ) from exc

        if len(query_vector) != self.config.embedding_dimension:
            raise RetrievalError(
                "Query embedding dimension does not match stored vectors.",
                status_code=500,
            )

        try:
            hits = self.repository.search_by_embedding(
                query_vector,
                document_id=document_id,
                limit=limit,
            )
        except RuntimeError as exc:
            raise RetrievalError(str(exc), status_code=503) from exc
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(
                "Database is unavailable for retrieval.",
                status_code=503,
            ) from exc

        results = [
            self._to_result(hit)
            for hit in hits
            if hit.similarity >= self.config.min_similarity
        ]

        if not results:
            return RetrievalSearchResponse(
                query=cleaned,
                results=[],
                retrieval_status="insufficient_evidence",
                detail=(
                    "No chunks met the minimum similarity threshold "
                    f"({self.config.min_similarity})."
                ),
            )

        return RetrievalSearchResponse(
            query=cleaned,
            results=results,
            retrieval_status="ok",
        )

    @staticmethod
    def _to_result(hit: SimilarChunkHit) -> RetrievalResult:
        return RetrievalResult(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            filename=hit.filename,
            chunk_index=hit.chunk_index,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
            similarity=hit.similarity,
        )
