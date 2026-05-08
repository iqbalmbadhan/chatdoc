import uuid
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.provider import ProviderConfig, ApiKey
from app.core.security import encrypt_api_key, decrypt_api_key
from app.providers.registry import DEFAULT_PROVIDERS


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

    async def get_default_provider(self) -> Tuple[Optional[ProviderConfig], Optional[str]]:
        result = await self.db.execute(
            select(ProviderConfig).where(ProviderConfig.is_default == True, ProviderConfig.is_enabled == True)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            return None, None

        key_result = await self.db.execute(
            select(ApiKey).where(ApiKey.provider == provider.name, ApiKey.is_active == True)
        )
        key_record = key_result.scalar_one_or_none()
        api_key = decrypt_api_key(key_record.encrypted_key) if key_record else ""

        return provider, api_key

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
