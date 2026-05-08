from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.auth.dependencies import get_admin_user

router = APIRouter()


@router.get("/overview")
async def get_overview(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await AnalyticsService(db).get_overview(days)


@router.get("/usage")
async def get_usage(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.analytics import UsageRecord
    from datetime import date, timedelta

    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(UsageRecord)
        .where(UsageRecord.date >= since)
        .order_by(UsageRecord.date.desc())
    )
    records = result.scalars().all()
    return {"records": records}
