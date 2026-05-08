from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def encrypt_api_key(key: str) -> str:
    """Simple reversible encryption for storing API keys."""
    import base64
    secret = settings.JWT_SECRET[:32].encode()
    key_bytes = key.encode()
    encrypted = bytes(a ^ b for a, b in zip(key_bytes, (secret * ((len(key_bytes) // 32) + 1))[:len(key_bytes)]))
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_api_key(encrypted: str) -> str:
    import base64
    secret = settings.JWT_SECRET[:32].encode()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
    decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, (secret * ((len(encrypted_bytes) // 32) + 1))[:len(encrypted_bytes)]))
    return decrypted.decode()
