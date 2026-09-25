"""Конфигурация resume-api (9to18)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 1
    DB_POOL_MAXSIZE: int = 8
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    S3_ENDPOINT_URL: str = ""
    S3_PUBLIC_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    # Rate limits (also overridable via RATE_LIMIT_{BUCKET}_REQUESTS / _WINDOW_SEC)
    RATE_LIMIT_AI_REQUESTS: int = 8
    RATE_LIMIT_AI_WINDOW_SEC: int = 60
    RATE_LIMIT_GENERATE_REQUESTS: int = 20
    RATE_LIMIT_GENERATE_WINDOW_SEC: int = 60
    RATE_LIMIT_PREVIEW_REQUESTS: int = 60
    RATE_LIMIT_PREVIEW_WINDOW_SEC: int = 60
    RATE_LIMIT_EXPORT_REQUESTS: int = 10
    RATE_LIMIT_EXPORT_WINDOW_SEC: int = 60

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
