from datetime import datetime, timezone, date, timedelta
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.analytics import UsageRecord
from app.models.chat import Message, Conversation
from app.models.document import Document
from app.models.visitor import Visitor, VisitorSession


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency_ms: int,
    ):
        today = date.today()
        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.date == today,
                UsageRecord.provider == provider,
                UsageRecord.model == model,
            )
        )
        record = result.scalar_one_or_none()

        if record:
            record.prompt_tokens += prompt_tokens
            record.completion_tokens += completion_tokens
            record.total_tokens += prompt_tokens + completion_tokens
            record.estimated_cost += cost
            record.request_count += 1
            record.avg_latency_ms = (record.avg_latency_ms * (record.request_count - 1) + latency_ms) / record.request_count
        else:
            record = UsageRecord(
                date=today,
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost=cost,
                avg_latency_ms=float(latency_ms),
            )
            self.db.add(record)

        await self.db.commit()

    async def get_overview(self, days: int = 30) -> dict:
        since = date.today() - timedelta(days=days)

        # Usage aggregates
        usage_result = await self.db.execute(
            select(
                func.sum(UsageRecord.total_tokens).label("total_tokens"),
                func.sum(UsageRecord.estimated_cost).label("total_cost"),
                func.sum(UsageRecord.request_count).label("total_requests"),
                func.avg(UsageRecord.avg_latency_ms).label("avg_latency"),
            ).where(UsageRecord.date >= since)
        )
        usage = usage_result.first()

        # Chat count
        chat_count = await self.db.scalar(select(func.count(Message.id)).where(Message.role == "assistant"))
        doc_count = await self.db.scalar(select(func.count(Document.id)))
        visitor_count = await self.db.scalar(select(func.count(Visitor.id)))

        # Provider breakdown
        provider_result = await self.db.execute(
            select(UsageRecord.provider, func.sum(UsageRecord.request_count).label("count"))
            .where(UsageRecord.date >= since)
            .group_by(UsageRecord.provider)
        )
        provider_breakdown = {row.provider: row.count for row in provider_result}

        # Daily stats
        daily_result = await self.db.execute(
            select(
                UsageRecord.date,
                func.sum(UsageRecord.request_count).label("chat_count"),
                func.sum(UsageRecord.total_tokens).label("token_count"),
                func.sum(UsageRecord.estimated_cost).label("cost"),
            )
            .where(UsageRecord.date >= since)
            .group_by(UsageRecord.date)
            .order_by(UsageRecord.date)
        )
        daily_stats = [
            {
                "date": str(row.date),
                "chat_count": row.chat_count or 0,
                "token_count": row.token_count or 0,
                "estimated_cost": float(row.cost or 0),
                "visitor_count": 0,
            }
            for row in daily_result
        ]

        return {
            "total_chats": chat_count or 0,
            "total_tokens": int(usage.total_tokens or 0),
            "total_cost": float(usage.total_cost or 0),
            "total_documents": doc_count or 0,
            "total_visitors": visitor_count or 0,
            "active_users_today": 0,
            "avg_latency_ms": float(usage.avg_latency or 0),
            "provider_breakdown": provider_breakdown,
            "daily_stats": daily_stats,
        }

    async def get_visitor_stats(self, days: int = 30) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        total = await self.db.scalar(select(func.count(Visitor.id)))
        unique_countries = await self.db.scalar(
            select(func.count(func.distinct(Visitor.country))).where(Visitor.country != None)
        )

        device_result = await self.db.execute(
            select(Visitor.device_type, func.count(Visitor.id).label("count"))
            .where(Visitor.device_type != None)
            .group_by(Visitor.device_type)
        )
        device_map = {r.device_type: r.count for r in device_result}
        total_dev = sum(device_map.values()) or 1

        browser_result = await self.db.execute(
            select(Visitor.browser, func.count(Visitor.id).label("count"))
            .where(Visitor.browser != None)
            .group_by(Visitor.browser)
            .order_by(desc("count"))
            .limit(10)
        )
        browser_breakdown = {r.browser: r.count for r in browser_result}

        country_result = await self.db.execute(
            select(Visitor.country, func.count(Visitor.id).label("count"))
            .where(Visitor.country != None)
            .group_by(Visitor.country)
            .order_by(desc("count"))
            .limit(15)
        )
        country_breakdown = {r.country: r.count for r in country_result}

        return {
            "total_visitors": total or 0,
            "unique_countries": unique_countries or 0,
            "mobile_pct": round(device_map.get("Mobile", 0) / total_dev * 100, 1),
            "desktop_pct": round(device_map.get("PC", 0) / total_dev * 100, 1),
            "tablet_pct": round(device_map.get("Tablet", 0) / total_dev * 100, 1),
            "browser_breakdown": browser_breakdown,
            "country_breakdown": country_breakdown,
            "device_breakdown": device_map,
            "daily_visitors": [],
        }
