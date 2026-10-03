"""Test doubles for heavy dependencies."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Sequence

from app.models.documents import DocumentMetadata, EmbeddedDocument
from app.services.llm_service import LLMError


@dataclass
class FakeLLMClient:
    """In-memory Ollama boundary — no real Gemma required."""

    model_name: str = "gemma3:4b"
    answer: str = "Normalization organizes tables to reduce redundancy."
    fail_with: LLMError | None = None
    generate_calls: list[dict[str, str]] = field(default_factory=list)
    ready_ok: bool = True

    def generate(self, *, system: str, user: str) -> str:
        self.generate_calls.append({"system": system, "user": user})
        if self.fail_with is not None:
            raise self.fail_with
        return self.answer

    def check_ready(self) -> dict[str, str]:
        if not self.ready_ok:
            raise LLMError(
                "The language model service is unavailable.",
                status_code=503,
            )
        return {
            "status": "ready",
            "provider": "ollama",
            "model": self.model_name,
        }


class FakeEmbeddingBackend:
    """Deterministic, normalized fake encoder — no model download required."""

    def __init__(
        self,
        *,
        model_name: str = "fake/bge-small-en-v1.5",
        dimension: int = 384,
    ) -> None:
        self._model_name = model_name
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool = True,
    ) -> list[list[float]]:
        return [self._vector_for(text, normalize=normalize_embeddings) for text in texts]

    def _vector_for(self, text: str, *, normalize: bool) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        # Expand digest into a stable pseudo-random unit vector.
        seed = list(digest)
        for index in range(self._dimension):
            byte = seed[index % len(seed)]
            mix = (byte + 31 * index + len(text)) % 256
            values.append((mix / 127.5) - 1.0)

        if not normalize:
            return values

        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            values[0] = 1.0
            return values
        return [value / norm for value in values]


@dataclass
class FakeDocumentRepository:
    """In-memory stand-in for PostgreSQL + pgvector persistence."""

    embedding_dimension: int = 384
    documents: dict[str, DocumentMetadata] = field(default_factory=dict)
    chunks_by_document: dict[str, list[dict]] = field(default_factory=dict)
    upsert_calls: int = 0
    fail_search: bool = False
    filenames: dict[str, str] = field(default_factory=dict)

    def upsert_embedded_document(
        self,
        metadata: DocumentMetadata,
        embedded: EmbeddedDocument,
    ) -> None:
        self.upsert_calls += 1
        if embedded.embedding_dimension not in (0, self.embedding_dimension):
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, "
                f"got {embedded.embedding_dimension}."
            )
        for chunk in embedded.chunks:
            if len(chunk.embedding) != self.embedding_dimension:
                raise ValueError(
                    f"Chunk {chunk.chunk_id} has embedding length "
                    f"{len(chunk.embedding)}, expected {self.embedding_dimension}."
                )

        self.documents[metadata.id] = metadata
        self.filenames[metadata.id] = metadata.filename
        # Replace chunks entirely for idempotent re-embeds.
        self.chunks_by_document[metadata.id] = [
            {
                "id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "text": chunk.text,
                "character_count": chunk.character_count,
                "embedding": list(chunk.embedding),
                "embedding_model": chunk.embedding_model,
            }
            for chunk in embedded.chunks
        ]

    def document_exists(self, document_id: str) -> bool:
        return document_id in self.documents or document_id in self.chunks_by_document

    def count_chunks(self, document_id: str) -> int:
        return len(self.chunks_by_document.get(document_id, []))

    def list_chunk_ids(self, document_id: str) -> list[str]:
        rows = self.chunks_by_document.get(document_id, [])
        return [row["id"] for row in sorted(rows, key=lambda item: item["chunk_index"])]

    def search_by_embedding(
        self,
        query_embedding: list[float],
        *,
        document_id: str | None = None,
        limit: int = 5,
    ) -> list:
        from app.services.document_repository import SimilarChunkHit

        if self.fail_search:
            raise RuntimeError("Database is unavailable for retrieval.")
        if len(query_embedding) != self.embedding_dimension:
            raise ValueError("Query embedding dimension mismatch.")

        candidates: list[dict] = []
        if document_id is not None:
            candidates.extend(self.chunks_by_document.get(document_id, []))
        else:
            for rows in self.chunks_by_document.values():
                candidates.extend(rows)

        scored: list[SimilarChunkHit] = []
        for row in candidates:
            similarity = _cosine_similarity(query_embedding, row["embedding"])
            scored.append(
                SimilarChunkHit(
                    chunk_id=row["id"],
                    document_id=row["document_id"],
                    filename=self.filenames.get(row["document_id"], "unknown.pdf"),
                    chunk_index=row["chunk_index"],
                    page_start=row["page_start"],
                    page_end=row["page_end"],
                    text=row["text"],
                    similarity=similarity,
                )
            )
        scored.sort(key=lambda hit: hit.similarity, reverse=True)
        return scored[:limit]

    def delete_document(self, document_id: str) -> None:
        self.documents.pop(document_id, None)
        self.chunks_by_document.pop(document_id, None)
        self.filenames.pop(document_id, None)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))

