"""PostgreSQL persistence for documents, chunks, and embeddings.

Filesystem JSON sidecars ({document_id}.chunks.json / .embeddings.json) remain
as a temporary dual-write for this phase and can be removed after semantic
retrieval (Phase 2.6) is verified against pgvector.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select, text

from app.db.database import get_engine, session_scope
from app.db.models import DocumentChunkRow, DocumentRow
from app.db.settings import get_embedding_dimension
from app.models.documents import DocumentMetadata, EmbeddedDocument


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
