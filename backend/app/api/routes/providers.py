import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.provider import ProviderConfigOut, ProviderConfigUpdate
from app.services.provider_service import ProviderService
from app.auth.dependencies import get_admin_user
from app.providers.registry import PROVIDER_REGISTRY, get_provider

router = APIRouter()


@router.get("")
async def list_providers(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = ProviderService(db)
    providers = await service.list_providers()
    if not providers:
        await service.seed_providers()
        providers = await service.list_providers()
    return providers


@router.patch("/{provider_id}")
async def update_provider(
    provider_id: uuid.UUID,
    body: ProviderConfigUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProviderService(db).update_provider(str(provider_id), body.model_dump(exclude_none=True))


@router.get("/{provider_name}/models")
async def get_provider_models(provider_name: str, admin: User = Depends(get_admin_user)):
    provider = get_provider(provider_name, api_key="")
    if not provider:
        raise HTTPException(404, "Provider not found")
    return {"models": provider.get_available_models()}


@router.post("/{provider_name}/validate")
async def validate_provider(provider_name: str, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    service = ProviderService(db)
    _, api_key = await service.get_default_provider()
    provider = get_provider(provider_name, api_key=api_key or "")
    if not provider:
        raise HTTPException(404, "Provider not found")
    valid = await provider.validate_key()
    return {"valid": valid, "provider": provider_name}
