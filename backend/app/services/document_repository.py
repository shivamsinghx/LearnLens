"""PostgreSQL persistence for documents, chunks, and embeddings.

Filesystem JSON sidecars ({document_id}.chunks.json / .embeddings.json) remain
as a temporary dual-write and can be removed after semantic retrieval is verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select, text

from app.db.database import get_engine, session_scope
from app.db.models import DocumentChunkRow, DocumentRow
from app.db.settings import get_embedding_dimension
from app.models.documents import DocumentMetadata, EmbeddedDocument


@dataclass(frozen=True)
class SimilarChunkHit:
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    page_start: int
    page_end: int
    text: str
    similarity: float


class DocumentRepository:
    """Primary persistence layer for embedded documents (PostgreSQL + pgvector)."""

    def __init__(self, *, embedding_dimension: int | None = None) -> None:
        self.embedding_dimension = embedding_dimension or get_embedding_dimension()

    def upsert_embedded_document(
        self,
        metadata: DocumentMetadata,
        embedded: EmbeddedDocument,
    ) -> None:
        """Insert/update a document and replace its chunks idempotently."""
        # Ensure engine/config is validated before opening a session.
        get_engine()

        if embedded.embedding_dimension and (
            embedded.embedding_dimension != self.embedding_dimension
        ):
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, "
                f"got {embedded.embedding_dimension}."
            )

        now = datetime.now(timezone.utc)
        with session_scope() as session:
            document = session.get(DocumentRow, metadata.id)
            if document is None:
                document = DocumentRow(
                    id=metadata.id,
                    filename=metadata.filename,
                    size=metadata.size_bytes,
                    content_type="application/pdf",
                    status=metadata.status,
                    created_at=now,
                    updated_at=now,
                )
                session.add(document)
            else:
                document.filename = metadata.filename
                document.size = metadata.size_bytes
                document.content_type = "application/pdf"
                document.status = metadata.status
                document.updated_at = now

            session.execute(
                delete(DocumentChunkRow).where(
                    DocumentChunkRow.document_id == metadata.id
                )
            )

            for chunk in embedded.chunks:
                if len(chunk.embedding) != self.embedding_dimension:
                    raise ValueError(
                        f"Chunk {chunk.chunk_id} has embedding length "
                        f"{len(chunk.embedding)}, expected {self.embedding_dimension}."
                    )
                session.add(
                    DocumentChunkRow(
                        id=chunk.chunk_id,
                        document_id=metadata.id,
                        chunk_index=chunk.chunk_index,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        text=chunk.text,
                        character_count=chunk.character_count,
                        embedding=chunk.embedding,
                        embedding_model=chunk.embedding_model,
                        created_at=now,
                    )
                )

    def get_document(self, document_id: str) -> DocumentRow | None:
        with session_scope() as session:
            document = session.get(DocumentRow, document_id)
            if document is not None:
                session.expunge(document)
            return document

    def document_exists(self, document_id: str) -> bool:
        with session_scope() as session:
            return session.get(DocumentRow, document_id) is not None

    def list_chunk_ids(self, document_id: str) -> list[str]:
        with session_scope() as session:
            rows = session.scalars(
                select(DocumentChunkRow.id)
                .where(DocumentChunkRow.document_id == document_id)
                .order_by(DocumentChunkRow.chunk_index)
            ).all()
            return list(rows)

    def count_chunks(self, document_id: str) -> int:
        return len(self.list_chunk_ids(document_id))

    def search_by_embedding(
        self,
        query_embedding: list[float],
        *,
        document_id: str | None = None,
        limit: int = 5,
    ) -> list[SimilarChunkHit]:
        """Return top-k chunks by pgvector cosine similarity (DB-side).

        Uses the cosine distance operator (`<=>` / `.cosine_distance`) so
        PostgreSQL can use `document_chunks_embedding_cosine_idx` (HNSW).
        Similarity is reported as ``1 - cosine_distance`` for L2-normalized vectors.
        """
        if len(query_embedding) != self.embedding_dimension:
            raise ValueError(
                f"Query embedding length {len(query_embedding)} does not match "
                f"configured dimension {self.embedding_dimension}."
            )
        if limit < 1:
            raise ValueError("limit must be >= 1")

        get_engine()
        distance = DocumentChunkRow.embedding.cosine_distance(query_embedding)
        stmt = (
            select(
                DocumentChunkRow.id,
                DocumentChunkRow.document_id,
                DocumentRow.filename,
                DocumentChunkRow.chunk_index,
                DocumentChunkRow.page_start,
                DocumentChunkRow.page_end,
                DocumentChunkRow.text,
                distance.label("distance"),
            )
            .join(DocumentRow, DocumentRow.id == DocumentChunkRow.document_id)
            .order_by(distance)
            .limit(limit)
        )
        if document_id is not None:
            stmt = stmt.where(DocumentChunkRow.document_id == document_id)

        with session_scope() as session:
            rows = session.execute(stmt).all()
            hits: list[SimilarChunkHit] = []
            for row in rows:
                distance_value = float(row.distance)
                similarity = max(0.0, min(1.0, 1.0 - distance_value))
                hits.append(
                    SimilarChunkHit(
                        chunk_id=row.id,
                        document_id=row.document_id,
                        filename=row.filename,
                        chunk_index=row.chunk_index,
                        page_start=row.page_start,
                        page_end=row.page_end,
                        text=row.text,
                        similarity=similarity,
                    )
                )
            return hits

    def delete_document(self, document_id: str) -> None:
        with session_scope() as session:
            document = session.get(DocumentRow, document_id)
            if document is not None:
                session.delete(document)

    def pgvector_available(self) -> bool:
        engine = get_engine()
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first()
            return row is not None
