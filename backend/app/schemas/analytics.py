from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DailyStats(BaseModel):
    date: date
    chat_count: int
    token_count: int
    estimated_cost: float
    visitor_count: int


class OverviewStats(BaseModel):
    total_chats: int
    total_tokens: int
    total_cost: float
    total_documents: int
    total_visitors: int
    active_users_today: int
    avg_latency_ms: float
    provider_breakdown: Dict[str, int]
    daily_stats: List[DailyStats]


class VisitorStats(BaseModel):
    total_visitors: int
    unique_countries: int
    mobile_pct: float
    desktop_pct: float
    tablet_pct: float
    browser_breakdown: Dict[str, int]
    country_breakdown: Dict[str, int]
    device_breakdown: Dict[str, int]
    daily_visitors: List[Dict[str, Any]]
