"""Local sentence-transformer embeddings for document chunks."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Protocol, Sequence

from app.models.documents import DocumentChunk, EmbeddedChunk

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def get_embedding_model_name() -> str:
    configured = os.getenv("EMBEDDING_MODEL", "").strip()
    return configured or DEFAULT_EMBEDDING_MODEL


class EmbeddingBackend(Protocol):
    """Minimal interface so tests can inject a fake encoder."""

    @property
    def model_name(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool = True,
    ) -> list[list[float]]: ...


class SentenceTransformerBackend:
    """Lazy wrapper around sentence-transformers."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        dimension = self._model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError(
                f"Could not determine embedding dimension for model {model_name!r}."
            )
        self._dimension = int(dimension)

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
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [vector.astype(float).tolist() for vector in vectors]


@dataclass(frozen=True)
class EmbeddingResult:
    chunks: list[EmbeddedChunk]
    embedding_dimension: int
    embedding_model: str
    status: str  # completed | empty | failed
    detail: str | None = None


class EmbeddingService:
    """Process-wide embedding helper with optional injectable backend."""

    _lock = threading.Lock()
    _shared_backend: EmbeddingBackend | None = None
    _shared_model_name: str | None = None

    def __init__(
        self,
        *,
        backend: EmbeddingBackend | None = None,
        model_name: str | None = None,
    ) -> None:
        self._injected_backend = backend
        self._model_name = model_name or get_embedding_model_name()

    @property
    def model_name(self) -> str:
        return self._get_backend().model_name

    @property
    def dimension(self) -> int:
        return self._get_backend().dimension

    def _get_backend(self) -> EmbeddingBackend:
        if self._injected_backend is not None:
            return self._injected_backend

        with EmbeddingService._lock:
            if (
                EmbeddingService._shared_backend is None
                or EmbeddingService._shared_model_name != self._model_name
            ):
                EmbeddingService._shared_backend = SentenceTransformerBackend(
                    self._model_name
                )
                EmbeddingService._shared_model_name = self._model_name
            return EmbeddingService._shared_backend

    def embed_text(self, text: str, *, normalize: bool = True) -> list[float]:
        vectors = self.embed_texts([text], normalize=normalize)
        return vectors[0]

    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        normalize: bool = True,
    ) -> list[list[float]]:
        backend = self._get_backend()
        return backend.encode(texts, normalize_embeddings=normalize)

    def embed_chunks(
        self,
        chunks: Sequence[DocumentChunk],
        *,
        normalize: bool = True,
    ) -> EmbeddingResult:
        if not chunks:
            return EmbeddingResult(
                chunks=[],
                embedding_dimension=self.dimension,
                embedding_model=self.model_name,
                status="empty",
                detail="No chunks were available to embed.",
            )

        # Keep empty/whitespace chunks aligned with outputs (still embed them).
        texts = [chunk.text for chunk in chunks]
        try:
            vectors = self.embed_texts(texts, normalize=normalize)
        except Exception as exc:  # noqa: BLE001 - surface model failures cleanly
            return EmbeddingResult(
                chunks=[],
                embedding_dimension=0,
                embedding_model=self._model_name,
                status="failed",
                detail=f"Embedding generation failed: {exc}",
            )

        if len(vectors) != len(chunks):
            return EmbeddingResult(
                chunks=[],
                embedding_dimension=0,
                embedding_model=self._model_name,
                status="failed",
                detail="Embedding backend returned an unexpected number of vectors.",
            )

        embedded: list[EmbeddedChunk] = []
        model_name = self.model_name
        for chunk, vector in zip(chunks, vectors, strict=True):
            embedded.append(
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text=chunk.text,
                    character_count=chunk.character_count,
                    embedding=vector,
                    embedding_model=model_name,
                )
            )

        return EmbeddingResult(
            chunks=embedded,
            embedding_dimension=self.dimension,
            embedding_model=model_name,
            status="completed",
        )
