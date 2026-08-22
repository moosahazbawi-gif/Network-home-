from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from .config import settings

try:
    from pwdlib import PasswordHash
    _password_hasher = PasswordHash.recommended()

    def hash_password(password: str) -> str:
        return _password_hasher.hash(password)

    def verify_password(password: str, password_hash: str) -> bool:
        return _password_hasher.verify(password, password_hash)
except Exception:
    from passlib.context import CryptContext
    _pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        return _pwd_context.hash(password)

    def verify_password(password: str, password_hash: str) -> bool:
        return _pwd_context.verify(password, password_hash)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    minutes = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    subject = payload.get("sub")
    if not subject:
        raise JWTError("invalid token subject")
    return subject
