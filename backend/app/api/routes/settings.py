import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings as app_settings
from app.core.redis import get_redis_client
from app.models.user import User
from app.schemas.settings import AppSettings
from app.auth.dependencies import get_admin_user

SETTINGS_KEY = "chatdoc:app_settings"

router = APIRouter()


def _defaults() -> dict:
    return {
        "chunk_size": app_settings.DEFAULT_CHUNK_SIZE,
        "chunk_overlap": app_settings.DEFAULT_CHUNK_OVERLAP,
        "top_k": app_settings.DEFAULT_TOP_K,
        "embedding_provider": "local",
        "embedding_model": app_settings.DEFAULT_EMBEDDING_MODEL,
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "ip_anonymization": False,
        "gdpr_consent": False,
        "log_retention_days": 90,
        "auto_delete_logs": False,
        "max_upload_size_mb": app_settings.MAX_UPLOAD_SIZE_MB,
        "rate_limit_per_minute": app_settings.RATE_LIMIT_PER_MINUTE,
        "system_prompt": None,
    }


async def _load() -> dict:
    redis = get_redis_client()
    raw = await redis.get(SETTINGS_KEY)
    if raw:
        stored = json.loads(raw)
        merged = _defaults()
        merged.update(stored)
        return merged
    return _defaults()


async def _save(data: dict) -> None:
    redis = get_redis_client()
    await redis.set(SETTINGS_KEY, json.dumps(data))


@router.get("/embedding-providers")
async def get_embedding_providers(admin: User = Depends(get_admin_user)):
    from app.providers.embeddings.registry import EMBEDDING_PROVIDER_OPTIONS
    return EMBEDDING_PROVIDER_OPTIONS


@router.get("", response_model=AppSettings)
async def get_settings(admin: User = Depends(get_admin_user)):
    data = await _load()
    return AppSettings(**data)


@router.put("", response_model=AppSettings)
async def update_settings(body: AppSettings, admin: User = Depends(get_admin_user)):
    await _save(body.model_dump())
    return body
