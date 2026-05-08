import uuid
import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.visitor import Visitor, VisitorSession


class VisitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _fingerprint(self, ip: str, user_agent: str) -> str:
        raw = f"{ip}:{user_agent}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _parse_user_agent(self, ua_string: str) -> dict:
        try:
            from user_agents import parse
            ua = parse(ua_string)
            return {
                "browser": ua.browser.family,
                "browser_version": ua.browser.version_string,
                "os": ua.os.family,
                "os_version": ua.os.version_string,
                "device_type": "Mobile" if ua.is_mobile else ("Tablet" if ua.is_tablet else "PC"),
                "is_bot": ua.is_bot,
            }
        except Exception:
            return {}

    def _anonymize_ip(self, ip: str) -> str:
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        return ip

    async def track(
        self,
        ip: str,
        user_agent: str,
        language: Optional[str] = None,
        screen_resolution: Optional[str] = None,
        timezone: Optional[str] = None,
        referrer: Optional[str] = None,
        landing_page: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Visitor:
        fp = self._fingerprint(ip, user_agent)
        ua_data = self._parse_user_agent(user_agent)

        result = await self.db.execute(select(Visitor).where(Visitor.fingerprint == fp))
        visitor = result.scalar_one_or_none()

        if visitor:
            visitor.visit_count += 1
            visitor.language = language or visitor.language
        else:
            visitor = Visitor(
                fingerprint=fp,
                ip_address=ip,
                ip_anonymized=self._anonymize_ip(ip),
                user_id=uuid.UUID(user_id) if user_id else None,
                browser=ua_data.get("browser"),
                browser_version=ua_data.get("browser_version"),
                os=ua_data.get("os"),
                os_version=ua_data.get("os_version"),
                device_type=ua_data.get("device_type"),
                is_bot=ua_data.get("is_bot", False),
                language=language,
                screen_resolution=screen_resolution,
                timezone=timezone,
                referrer=referrer,
                landing_page=landing_page,
                user_agent=user_agent,
            )
            self.db.add(visitor)

        await self.db.commit()
        await self.db.refresh(visitor)
        return visitor

    async def get_active_sessions(self) -> int:
        from datetime import datetime, timezone, timedelta
        threshold = datetime.now(timezone.utc) - timedelta(minutes=15)
        result = await self.db.execute(
            select(func.count(VisitorSession.id))
            .where(VisitorSession.started_at >= threshold, VisitorSession.ended_at == None)
        )
        return result.scalar() or 0

    async def list_visitors(self, page: int = 1, page_size: int = 50) -> tuple:
        total = await self.db.scalar(select(func.count(Visitor.id)))
        result = await self.db.execute(
            select(Visitor)
            .order_by(Visitor.last_seen.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total
