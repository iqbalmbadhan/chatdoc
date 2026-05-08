import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentListResponse, DocumentUpdate
from app.services.document_service import DocumentService
from app.auth.dependencies import get_admin_user

router = APIRouter()


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form(""),
    description: str = Form(""),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    service = DocumentService(db)
    doc = await service.upload_document(content, file.filename, owner_id=str(admin.id))

    if tags:
        doc.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if description:
        doc.description = description
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    items, total = await service.list_documents(page, page_size, status)
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats")
async def document_stats(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    return await DocumentService(db).get_stats()


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: uuid.UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    doc = await DocumentService(db).get_document(str(doc_id))
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.patch("/{doc_id}", response_model=DocumentOut)
async def update_document(doc_id: uuid.UUID, body: DocumentUpdate, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.document import Document
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    if body.tags is not None:
        doc.tags = body.tags
    if body.description is not None:
        doc.description = body.description
    if body.is_active is not None:
        doc.is_active = body.is_active
    await db.commit()
    await db.refresh(doc)
    return doc


@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: uuid.UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    from app.services.document_tasks import index_document_task
    index_document_task.delay(str(doc_id))
    return {"message": "Re-indexing started"}


@router.delete("/{doc_id}")
async def delete_document(doc_id: uuid.UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    await DocumentService(db).delete_document(str(doc_id))
    return {"message": "Document deleted"}
