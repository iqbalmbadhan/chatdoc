import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Visitor(Base):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("ix_visitors_last_seen", "last_seen"),
        Index("ix_visitors_country", "country"),
        Index("ix_visitors_device_type", "device_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Identity
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    ip_anonymized: Mapped[str] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Geo
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str] = mapped_column(String(10), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=True)

    # Device / Browser
    browser: Mapped[str] = mapped_column(String(100), nullable=True)
    browser_version: Mapped[str] = mapped_column(String(50), nullable=True)
    os: Mapped[str] = mapped_column(String(100), nullable=True)
    os_version: Mapped[str] = mapped_column(String(50), nullable=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=True)  # mobile/tablet/desktop
    screen_resolution: Mapped[str] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    # Traffic
    referrer: Mapped[str] = mapped_column(Text, nullable=True)
    landing_page: Mapped[str] = mapped_column(String(500), nullable=True)

    # Stats
    visit_count: Mapped[int] = mapped_column(Integer, default=1)
    chat_count: Mapped[int] = mapped_column(Integer, default=0)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class VisitorSession(Base):
    __tablename__ = "visitor_sessions"
    __table_args__ = (
        Index("ix_visitor_sessions_started_at", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("visitors.id"), nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    pages_visited: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
