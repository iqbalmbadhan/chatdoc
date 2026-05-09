import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None
    session_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class SourceDocument(BaseModel):
    doc_id: str
    filename: str
    page: Optional[int] = None
    score: Optional[float] = None
    excerpt: Optional[str] = None


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    provider: Optional[str]
    model: Optional[str]
    total_tokens: Optional[int] = 0
    estimated_cost: Optional[float] = 0.0
    latency_ms: Optional[int] = 0
    source_documents: Optional[List[Any]] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: List[MessageOut]


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageOut
