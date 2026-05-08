import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.provider import ApiKeyCreate, ApiKeyOut
from app.services.provider_service import ProviderService
from app.auth.dependencies import get_admin_user

router = APIRouter()


@router.get("", response_model=list[ApiKeyOut])
async def list_keys(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    return await ProviderService(db).list_keys()


@router.post("", response_model=ApiKeyOut)
async def create_key(body: ApiKeyCreate, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    return await ProviderService(db).save_api_key(body.provider, body.key, body.label)


@router.delete("/{key_id}")
async def delete_key(key_id: uuid.UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await ProviderService(db).delete_key(str(key_id))
    return {"message": "Key deleted"}
