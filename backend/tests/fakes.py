"""Test doubles for heavy dependencies."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Sequence

from app.models.documents import DocumentMetadata, EmbeddedDocument


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

    def count_chunks(self, document_id: str) -> int:
        return len(self.chunks_by_document.get(document_id, []))

    def list_chunk_ids(self, document_id: str) -> list[str]:
        rows = self.chunks_by_document.get(document_id, [])
        return [row["id"] for row in sorted(rows, key=lambda item: item["chunk_index"])]

    def delete_document(self, document_id: str) -> None:
        self.documents.pop(document_id, None)
        self.chunks_by_document.pop(document_id, None)

