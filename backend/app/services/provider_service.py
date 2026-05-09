import json
import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provider import ProviderConfig, ApiKey
from app.core.security import encrypt_api_key, decrypt_api_key
from app.providers.chat.registry import DEFAULT_PROVIDERS
from app.schemas.settings import SETTINGS_REDIS_KEY


class ProviderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_providers(self):
        for p in DEFAULT_PROVIDERS:
            result = await self.db.execute(select(ProviderConfig).where(ProviderConfig.name == p["name"]))
            if not result.scalar_one_or_none():
                config = ProviderConfig(
                    name=p["name"],
                    display_name=p["display_name"],
                    default_model=p["default_model"],
                    default_embedding_model=p.get("default_embedding_model"),
                    is_enabled=p["name"] == "ollama",
                    is_default=p["name"] == "ollama",
                )
                self.db.add(config)
        await self.db.commit()

    async def get_embedding_config(self) -> Tuple[str, str, str]:
        """Return (provider_name, model, api_key) for the configured embedding provider."""
        from app.core.redis import get_redis_client
        from app.core.config import settings as app_config

        redis = get_redis_client()
        raw = await redis.get(SETTINGS_REDIS_KEY)
        data = json.loads(raw) if raw else {}

        provider_name = data.get("embedding_provider", "local")
        model = data.get("embedding_model", app_config.DEFAULT_EMBEDDING_MODEL)

        api_key = ""
        if provider_name not in ("local", "ollama"):
            key_result = await self.db.execute(
                select(ApiKey).where(ApiKey.provider == provider_name, ApiKey.is_active == True)
            )
            key_record = key_result.scalar_one_or_none()
            if key_record:
                api_key = decrypt_api_key(key_record.encrypted_key)

        return provider_name, model, api_key

    async def get_default_provider(self) -> Tuple[Optional[ProviderConfig], Optional[str]]:
        result = await self.db.execute(
            select(ProviderConfig).where(ProviderConfig.is_default == True, ProviderConfig.is_enabled == True)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            return None, None

        api_key = await self.get_api_key(provider.name)
        return provider, api_key

    async def get_provider_config(self, name: str) -> Tuple[Optional[ProviderConfig], Optional[str]]:
        result = await self.db.execute(select(ProviderConfig).where(ProviderConfig.name == name))
        provider = result.scalar_one_or_none()
        if not provider:
            return None, None
        
        api_key = await self.get_api_key(name)
        return provider, api_key

    async def get_api_key(self, provider: str) -> str:
        if provider in ("ollama", "local"):
            return ""
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.provider == provider, ApiKey.is_active == True)
        )
        record = result.scalar_one_or_none()
        return decrypt_api_key(record.encrypted_key) if record else ""

    async def list_providers(self):
        result = await self.db.execute(select(ProviderConfig))
        return result.scalars().all()

    async def update_provider(self, provider_id: str, updates: dict) -> ProviderConfig:
        result = await self.db.execute(select(ProviderConfig).where(ProviderConfig.id == uuid.UUID(provider_id)))
        provider = result.scalar_one_or_none()
        if not provider:
            raise ValueError("Provider not found")

        if updates.get("is_default"):
            all_result = await self.db.execute(select(ProviderConfig))
            for p in all_result.scalars().all():
                p.is_default = False

        for k, v in updates.items():
            if v is not None and hasattr(provider, k):
                setattr(provider, k, v)

        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def save_api_key(self, provider: str, key: str, label: Optional[str] = None) -> ApiKey:
        encrypted = encrypt_api_key(key)
        hint = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"

        existing = await self.db.execute(
            select(ApiKey).where(ApiKey.provider == provider, ApiKey.is_active == True)
        )
        existing_key = existing.scalar_one_or_none()

        if existing_key:
            existing_key.encrypted_key = encrypted
            existing_key.key_hint = hint
            existing_key.label = label
            await self.db.commit()
            return existing_key

        api_key = ApiKey(provider=provider, encrypted_key=encrypted, key_hint=hint, label=label)
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def list_keys(self):
        result = await self.db.execute(select(ApiKey))
        return result.scalars().all()

    async def delete_key(self, key_id: str):
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == uuid.UUID(key_id)))
        key = result.scalar_one_or_none()
        if key:
            self.db.delete(key)  # session.delete() is synchronous; no await
            await self.db.commit()
