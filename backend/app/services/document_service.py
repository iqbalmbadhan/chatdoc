import uuid
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.config import settings
from app.models.document import Document
from app.rag.document_processor import DocumentProcessor
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore

logger = structlog.get_logger()


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = VectorStore()

    async def upload_document(self, file_content: bytes, filename: str, owner_id: Optional[str] = None) -> Document:
        file_type = DocumentProcessor.get_file_type(filename)
        if file_type not in DocumentProcessor.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: .{file_type}")

        doc_id = uuid.uuid4()
        safe_name = f"{doc_id}_{filename}"
        upload_path = Path(settings.STORAGE_PATH) / "uploads" / safe_name

        upload_path.parent.mkdir(parents=True, exist_ok=True)
        with open(upload_path, "wb") as f:
            f.write(file_content)

        doc = Document(
            id=doc_id,
            filename=safe_name,
            original_filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            file_path=str(upload_path),
            status="pending",
            owner_id=uuid.UUID(owner_id) if owner_id else None,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Trigger async indexing
        from app.services.document_tasks import index_document_task
        index_document_task.delay(str(doc_id))

        return doc

    async def index_document(self, doc_id: str, chunk_size: int = None, chunk_overlap: int = None, embedding_model: str = None) -> Document:
        result = await self.db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
        embedding_model = embedding_model or settings.DEFAULT_EMBEDDING_MODEL

        doc.status = "processing"
        doc.chunk_size = chunk_size
        doc.chunk_overlap = chunk_overlap
        doc.embedding_model = embedding_model
        await self.db.commit()

        try:
            text, page_count = DocumentProcessor.extract_text(doc.file_path, doc.file_type)
            text = DocumentProcessor.clean_text(text)
            chunks = DocumentProcessor.chunk_text(text, chunk_size, chunk_overlap)
            token_count = DocumentProcessor.estimate_tokens(text)

            dimension = EmbeddingService.get_dimension(embedding_model)
            await self.vector_store.ensure_collection(dimension=dimension)

            embeddings = await EmbeddingService.embed_texts_local(chunks, embedding_model)

            await self.vector_store.upsert_chunks(
                doc_id=str(doc.id),
                chunks=chunks,
                embeddings=embeddings,
                metadata={"filename": doc.original_filename, "file_type": doc.file_type},
            )

            doc.status = "indexed"
            doc.page_count = page_count
            doc.chunk_count = len(chunks)
            doc.token_count = token_count
            doc.char_count = len(text)
            doc.indexed_at = datetime.now(timezone.utc)
            doc.error_message = None
            await self.db.commit()

            logger.info("Document indexed", doc_id=doc_id, chunks=len(chunks))
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            await self.db.commit()
            logger.error("Document indexing failed", doc_id=doc_id, error=str(e))
            raise

        return doc

    async def delete_document(self, doc_id: str):
        result = await self.db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found")

        await self.vector_store.delete_document(doc_id)

        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        await self.db.delete(doc)
        await self.db.commit()

    async def list_documents(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> tuple:
        query = select(Document)
        if status:
            query = query.where(Document.status == status)
        query = query.order_by(desc(Document.created_at))

        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_document(self, doc_id: str) -> Optional[Document]:
        result = await self.db.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))
        return result.scalar_one_or_none()

    async def get_stats(self) -> dict:
        result = await self.db.execute(
            select(
                func.count(Document.id).label("total"),
                func.sum(Document.file_size).label("total_size"),
                func.sum(Document.chunk_count).label("total_chunks"),
                func.sum(Document.token_count).label("total_tokens"),
            )
        )
        row = result.first()
        return {
            "total_documents": row.total or 0,
            "total_size_bytes": row.total_size or 0,
            "total_chunks": row.total_chunks or 0,
            "total_tokens": row.total_tokens or 0,
        }
