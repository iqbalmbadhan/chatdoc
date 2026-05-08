import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.models.user import User
from app.models.chat import Message, Conversation
from app.models.system_log import SystemLog, AdminActivityLog
from app.auth.dependencies import get_admin_user
import csv
import io

router = APIRouter()


@router.get("/chats")
async def list_chat_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    search: Optional[str] = None,
    provider: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message).where(Message.role == "assistant")
    if search:
        query = query.where(Message.content.ilike(f"%{search}%"))
    if provider:
        query = query.where(Message.provider == provider)
    query = query.order_by(desc(Message.created_at))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()
    return {"items": items, "total": total, "page": page}


@router.get("/chats/export")
async def export_chat_logs(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.role == "assistant").order_by(desc(Message.created_at)).limit(10000)
    )
    messages = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "conversation_id", "content", "provider", "model", "total_tokens", "estimated_cost", "latency_ms", "created_at"])
    for m in messages:
        writer.writerow([m.id, m.conversation_id, m.content[:200], m.provider, m.model, m.total_tokens, m.estimated_cost, m.latency_ms, m.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chat_logs.csv"},
    )


@router.delete("/chats/{message_id}")
async def delete_chat_log(message_id: uuid.UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        await db.delete(msg)
        await db.commit()
    return {"message": "Deleted"}


@router.get("/system")
async def list_system_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    level: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SystemLog)
    if level:
        query = query.where(SystemLog.level == level)
    query = query.order_by(desc(SystemLog.created_at))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return {"items": result.scalars().all(), "total": total}


@router.get("/activity")
async def admin_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(50),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AdminActivityLog).order_by(desc(AdminActivityLog.created_at))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return {"items": result.scalars().all(), "total": total}
