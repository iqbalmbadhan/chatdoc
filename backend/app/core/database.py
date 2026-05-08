import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = structlog.get_logger()

# At 10k req/min (~167 req/s) with typical 50ms DB queries, we need enough
# connections to handle concurrent load without queuing. pool_size=30 keeps
# ~30 persistent connections; max_overflow=60 allows 60 more under burst load.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=30,
    max_overflow=60,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    from app.models import user, document, chat as chat_model, analytics, visitor, system_log  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.auth_service import AuthService
    async with AsyncSessionLocal() as session:
        try:
            await AuthService.seed_admin(session)
        except Exception:
            logger.exception("Failed to seed admin user")
