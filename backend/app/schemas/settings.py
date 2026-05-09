from typing import Optional
from pydantic import BaseModel

SETTINGS_REDIS_KEY = "chatdoc:app_settings"


class AppSettings(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    ip_anonymization: bool = False
    gdpr_consent: bool = False
    log_retention_days: int = 90
    auto_delete_logs: bool = False
    max_upload_size_mb: int = 50
    rate_limit_per_minute: int = 60
    system_prompt: Optional[str] = None
