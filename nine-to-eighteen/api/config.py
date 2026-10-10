"""Конфигурация независимого API 9to18.ru."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 2
    DB_POOL_MAXSIZE: int = 16
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    MAX_UPLOAD_IMAGE_BYTES: int = 5 * 1024 * 1024
    S3_ENDPOINT_URL: str = ""
    S3_PUBLIC_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    # Dev only: include password-reset token in forgot-password JSON (no SMTP).
    DEV_EXPOSE_RESET_TOKEN: bool = False
    # Auth / contact rate limits (keyed by client IP)
    RATE_LIMIT_AUTH_REQUESTS: int = 20
    RATE_LIMIT_AUTH_WINDOW_SEC: int = 60
    RATE_LIMIT_CONTACT_REQUESTS: int = 10
    RATE_LIMIT_CONTACT_WINDOW_SEC: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def validate_required_secrets() -> None:
    missing: list[str] = []
    if not (settings.DATABASE_URL or "").strip():
        missing.append("DATABASE_URL")
    if not (settings.JWT_SECRET_KEY or "").strip():
        missing.append("JWT_SECRET_KEY")
    if missing:
        raise RuntimeError(
            "Missing required secrets (set via .env or environment): "
            + ", ".join(missing)
        )


validate_required_secrets()
