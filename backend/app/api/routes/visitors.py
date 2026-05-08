from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.visitor_service import VisitorService
from app.services.analytics_service import AnalyticsService
from app.auth.dependencies import get_admin_user

router = APIRouter()


@router.post("/track")
async def track_visitor(
    request: Request,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    visitor = await VisitorService(db).track(
        ip=ip,
        user_agent=ua,
        language=body.get("language"),
        screen_resolution=body.get("screen_resolution"),
        timezone=body.get("timezone"),
        referrer=body.get("referrer"),
        landing_page=body.get("landing_page"),
    )
    return {"visitor_id": str(visitor.id)}


@router.get("")
async def list_visitors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await VisitorService(db).list_visitors(page, page_size)
    return {"items": items, "total": total}


@router.get("/stats")
async def visitor_stats(
    days: int = Query(30),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService(db).get_visitor_stats(days)


@router.get("/active")
async def active_sessions(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    count = await VisitorService(db).get_active_sessions()
    return {"active_sessions": count}
