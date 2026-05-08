import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    page_count: int
    chunk_count: int
    token_count: int
    tags: List[str]
    description: Optional[str]
    is_active: bool
    embedding_model: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int
