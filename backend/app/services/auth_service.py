import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.models.user import User

logger = structlog.get_logger()


class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None

        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        return user

    @staticmethod
    async def seed_admin(db: AsyncSession):
        result = await db.execute(select(User).where(User.role == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                full_name="Admin",
                must_change_password=True,
                is_active=True,
            )
            db.add(admin)
            await db.commit()
            logger.info("Default admin created", email=settings.DEFAULT_ADMIN_EMAIL)

    @staticmethod
    def generate_tokens(user: User) -> dict:
        return {
            "access_token": create_access_token(str(user.id), user.role),
            "refresh_token": create_refresh_token(str(user.id)),
            "token_type": "bearer",
        }
