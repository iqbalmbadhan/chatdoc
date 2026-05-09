import asyncio
from app.core.celery_app import celery_app
import structlog

logger = structlog.get_logger()

# Create a persistent event loop for the worker process
try:
    _loop = asyncio.get_event_loop()
except RuntimeError:
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)

@celery_app.task(name="index_document", bind=True, max_retries=3)
def index_document_task(self, doc_id: str):
    """Celery task to index a document in the background."""
    async def run():
        from app.core.database import AsyncSessionLocal
        from app.core.redis import init_redis, get_redis_client
        from app.services.document_service import DocumentService
        
        try:
            get_redis_client()
        except RuntimeError:
            await init_redis()
            
        async with AsyncSessionLocal() as db:
            service = DocumentService(db)
            await service.index_document(doc_id)

    try:
        _loop.run_until_complete(run())
    except Exception as exc:
        logger.error("Indexing task failed", doc_id=doc_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
