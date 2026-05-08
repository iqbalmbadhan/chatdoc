from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.models.user import User
from app.rag.vector_store import VectorStore
from app.auth.dependencies import get_admin_user

router = APIRouter()


@router.get("/health")
async def system_health(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    status = {}

    # PostgreSQL
    try:
        await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        status["postgres"] = "healthy"
    except Exception as e:
        status["postgres"] = f"error: {e}"

    # Redis
    try:
        from app.core.redis import get_redis_client
        redis = await get_redis_client()
        await redis.ping()
        status["redis"] = "healthy"
    except Exception as e:
        status["redis"] = f"error: {e}"

    # Qdrant
    try:
        vs = VectorStore()
        info = await vs.get_collection_info()
        status["qdrant"] = "healthy"
        status["qdrant_info"] = info
    except Exception as e:
        status["qdrant"] = f"error: {e}"

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            status["ollama"] = "healthy" if r.status_code == 200 else "unavailable"
    except Exception:
        status["ollama"] = "unavailable"

    return status


@router.get("/info")
async def system_info(admin: User = Depends(get_admin_user)):
    import platform
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "python_version": platform.python_version(),
        "platform": platform.system(),
    }
