import asyncio
from app.core.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="index_document", bind=True, max_retries=3)
def index_document_task(self, doc_id: str):
    """Celery task to index a document in the background."""
    async def run():
        from app.core.database import AsyncSessionLocal
        from app.services.document_service import DocumentService
        async with AsyncSessionLocal() as db:
            service = DocumentService(db)
            await service.index_document(doc_id)

    try:
        asyncio.run(run())
    except Exception as exc:
        logger.error("Indexing task failed", doc_id=doc_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
