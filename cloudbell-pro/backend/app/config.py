import os
from dataclasses import dataclass


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CloudBell Pro")
    environment: str = os.getenv("ENVIRONMENT", "production")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://cloudbell:cloudbell@postgres:5432/cloudbell")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0"))
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    data_dir: str = os.getenv("DATA_DIR", "/data")
    max_download_bytes: int = int(os.getenv("MAX_DOWNLOAD_BYTES", str(5 * 1024 * 1024 * 1024)))
    download_user_agent: str = os.getenv("DOWNLOAD_USER_AGENT", "CloudBellPro/1.0")
    download_timeout_seconds: int = int(os.getenv("DOWNLOAD_TIMEOUT_SECONDS", "20"))
    download_connect_timeout_seconds: int = int(os.getenv("DOWNLOAD_CONNECT_TIMEOUT_SECONDS", "10"))
    download_max_redirects: int = int(os.getenv("DOWNLOAD_MAX_REDIRECTS", "5"))
    download_allow_http: bool = _bool("DOWNLOAD_ALLOW_HTTP", "false")
    bootstrap_admin_email: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "")
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    cleanup_retention_days: int = int(os.getenv("CLEANUP_RETENTION_DAYS", "30"))
    enable_beat: bool = _bool("ENABLE_BEAT", "false")


settings = Settings()
