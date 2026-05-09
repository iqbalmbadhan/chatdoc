from typing import Optional

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_pool: Optional[aioredis.ConnectionPool] = None
_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _pool, _client
    _pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=200,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )
    _client = aioredis.Redis(connection_pool=_pool)
    await _client.ping()
    logger.info("Redis connected")


async def close_redis() -> None:
    global _client, _pool
    if _client:
        await _client.aclose()
        _client = None
    if _pool:
        await _pool.aclose()
        _pool = None
    logger.info("Redis disconnected")


def get_redis_client() -> aioredis.Redis:
    if _client is None:
        # We can't await here because get_redis_client is sync, 
        # but we can return a new unawaited client or raise.
        # Actually we should raise if it's strictly sync and not initialized.
        raise RuntimeError("Redis not initialised. Call init_redis() first.")
    return _client


async def get_redis():
    """FastAPI dependency that yields the shared Redis client."""
    yield get_redis_client()
