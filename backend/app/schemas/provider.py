import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ProviderConfigOut(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    is_enabled: bool
    is_default: bool
    default_model: Optional[str]
    default_embedding_model: Optional[str]
    settings: Dict[str, Any]
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    default_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ApiKeyCreate(BaseModel):
    provider: str
    key: str
    label: Optional[str] = None


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    provider: str
    label: Optional[str]
    key_hint: Optional[str]
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
