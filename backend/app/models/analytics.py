import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Date, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"
    # Composite index to speed up the per-day/provider/model aggregation queries
    __table_args__ = (
        Index("ix_usage_records_date_provider_model", "date", "provider", "model"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, default=1)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
