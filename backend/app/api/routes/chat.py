import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ConversationOut, ConversationDetail, MessageOut
from app.services.chat_service import ChatService
from app.services.visitor_service import VisitorService
from app.auth.dependencies import get_optional_user

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    # Track visitor
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    visitor = await VisitorService(db).track(ip=ip, user_agent=ua)

    service = ChatService(db)
    result = await service.chat(
        query=body.message,
        conversation_id=body.conversation_id,
        session_id=body.session_id,
        user_id=str(user.id) if user else None,
        provider_name=body.provider,
        model_name=body.model,
        visitor_id=str(visitor.id),
    )
    return result


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    service = ChatService(db)

    async def generate():
        yield f"data: {{'conversation_id': '{body.conversation_id}'}}\n\n"
        async for token in service.chat_stream(
            query=body.message,
            conversation_id=body.conversation_id,
            session_id=body.session_id,
            user_id=str(user.id) if user else None,
            provider_name=body.provider,
            model_name=body.model,
        ):
            import json
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20),
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    service = ChatService(db)
    items, total = await service.list_conversations(
        user_id=str(user.id) if user else None,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total}


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    messages = await ChatService(db).get_conversation_messages(conv_id)
    return {"messages": messages}
