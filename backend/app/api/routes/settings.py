from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings as app_settings
from app.models.user import User
from app.schemas.settings import AppSettings
from app.auth.dependencies import get_admin_user

# In a real app these would be stored in DB, for MVP we use a simple in-memory store
_settings_store: dict = {}

router = APIRouter()


@router.get("", response_model=AppSettings)
async def get_settings(admin: User = Depends(get_admin_user)):
    return AppSettings(
        chunk_size=_settings_store.get("chunk_size", app_settings.DEFAULT_CHUNK_SIZE),
        chunk_overlap=_settings_store.get("chunk_overlap", app_settings.DEFAULT_CHUNK_OVERLAP),
        top_k=_settings_store.get("top_k", app_settings.DEFAULT_TOP_K),
        embedding_model=_settings_store.get("embedding_model", app_settings.DEFAULT_EMBEDDING_MODEL),
        default_provider=_settings_store.get("default_provider", "openai"),
        default_model=_settings_store.get("default_model", "gpt-4o-mini"),
        ip_anonymization=_settings_store.get("ip_anonymization", False),
        gdpr_consent=_settings_store.get("gdpr_consent", False),
        log_retention_days=_settings_store.get("log_retention_days", 90),
        auto_delete_logs=_settings_store.get("auto_delete_logs", False),
        max_upload_size_mb=_settings_store.get("max_upload_size_mb", app_settings.MAX_UPLOAD_SIZE_MB),
        rate_limit_per_minute=_settings_store.get("rate_limit_per_minute", app_settings.RATE_LIMIT_PER_MINUTE),
        system_prompt=_settings_store.get("system_prompt"),
    )


@router.put("", response_model=AppSettings)
async def update_settings(body: AppSettings, admin: User = Depends(get_admin_user)):
    _settings_store.update(body.model_dump())
    return body
