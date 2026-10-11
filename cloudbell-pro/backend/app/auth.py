from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from .config import settings


# Password hashing
#
# مسیر اصلی: pwdlib + Argon2
# مسیر جایگزین: Passlib در صورتی که pwdlib نصب نشده باشد.
try:
    from pwdlib import PasswordHash

    _password_hasher = PasswordHash.recommended()

    def hash_password(password: str) -> str:
        return _password_hasher.hash(password)

    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return _password_hasher.verify(password, password_hash)
        except (ValueError, TypeError):
            return False

except ImportError:
    from passlib.context import CryptContext

    _password_context = CryptContext(
        schemes=["argon2", "bcrypt"],
        deprecated="auto",
    )

    def hash_password(password: str) -> str:
        return _password_context.hash(password)

    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return _password_context.verify(password, password_hash)
        except (ValueError, TypeError):
            return False


def create_access_token(
    subject: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    ساخت توکن JWT برای کاربر.
    subject در این پروژه معمولاً ایمیل کاربر است.
    """
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("JWT subject must be a non-empty string")

    minutes = (
        settings.access_token_expire_minutes
        if expires_minutes is None
        else expires_minutes
    )

    if minutes <= 0:
        raise ValueError("Token expiration must be greater than zero")

    expire_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    payload = {
        "sub": subject.strip(),
        "exp": expire_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> str:
    """
    اعتبارسنجی و decode کردن JWT.

    در صورت نامعتبر بودن توکن، منقضی شدن آن،
    یا نبودن subject، خطای JWTError ایجاد می‌شود.
    """
    if not isinstance(token, str) or not token.strip():
        raise JWTError("Empty token")

    payload = jwt.decode(
        token.strip(),
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options={
            "require_sub": True,
            "require_exp": True,
        },
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.strip():
        raise JWTError("Invalid token subject")

    return subject.strip()
