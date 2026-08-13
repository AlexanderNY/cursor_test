from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Конфигурация Core сервиса из переменных окружения."""
    
    # База данных (обязательно через env / .env)
    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 2
    DB_POOL_MAXSIZE: int = 20
    
    # API Gateway URL для healthcheck запросов
    API_GATEWAY_URL: str = "http://localhost:8000"
    
    # JWT настройки (должны совпадать с auth SECRET_KEY)
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    
    # Список сервисов для healthcheck
    HEALTHCHECK_SERVICES: List[str] = [
        "auth",
        "core",
        "api-gateway",
        "tg-bot",
        "vk-bot",
        "wp-bot",
        "url-bot",
        "tw-bot",
        "scheduler"
    ]
    
    # URL сервисов для прямого healthcheck
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    TG_BOT_SERVICE_URL: str = "http://localhost:8004"
    VK_BOT_SERVICE_URL: str = "http://localhost:8005"
    WP_BOT_SERVICE_URL: str = "http://localhost:8006"
    URL_BOT_SERVICE_URL: str = "http://localhost:8007"
    TW_BOT_SERVICE_URL: str = "http://localhost:8011"
    SCHEDULER_SERVICE_URL: str = "http://localhost:8003"
    COLLECTOR_SERVICE_URL: str = "http://localhost:8009"
    PROCESSOR_SERVICE_URL: str = "http://localhost:8010"

    # Healthcheck: кэш агрегата и circuit breaker для внешних /health
    HEALTHCHECK_CACHE_TTL_SECONDS: int = 45
    HEALTHCHECK_REQUEST_TIMEOUT_SECONDS: float = 5.0
    HEALTHCHECK_CIRCUIT_FAILURE_THRESHOLD: int = 3
    HEALTHCHECK_CIRCUIT_RECOVERY_SECONDS: float = 60.0
    
    # Threads (Meta) OAuth
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    THREADS_OAUTH_REDIRECT_URI: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # VK OAuth (user_access_token для wall/photos на стене группы)
    VK_APP_ID: str = ""
    VK_APP_SECRET: str = ""
    VK_OAUTH_REDIRECT_URI: str = ""
    # Публичный URL gateway (как его видит браузер и VK), не внутренний http://gateway:8000
    VK_PUBLIC_GATEWAY_URL: str = "http://localhost:8000"

    # X (Twitter) OAuth 2.0 PKCE (Core callback обменивает code на токены)
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_OAUTH_REDIRECT_URI: str = ""

    # Базовый URL для ссылок в RSS Дзен (item link)
    RSS_BASE_URL: str = "http://localhost:8002"

    # S3-совместимое хранилище (MinIO по умолчанию на 172.20.10.200). Пустые ACCESS_KEY/SECRET_KEY — хранилище отключено (fallback на локальный диск).
    S3_ENDPOINT_URL: str = "http://172.20.10.200:9000"
    # Публичный endpoint для браузера (presigned URL). В Docker API — http://minio:9000, в UI — http://localhost:9000.
    S3_PUBLIC_ENDPOINT_URL: str = "http://localhost:9000"
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def validate_required_secrets() -> None:
    """Fail-fast, если критичные секреты не заданы через окружение."""
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


def get_vk_oauth_redirect_uri(public_gateway_url: Optional[str] = None) -> str:
    """Redirect URI для VK OAuth: профиль/UI, явный VK_OAUTH_REDIRECT_URI или VK_PUBLIC_GATEWAY_URL."""
    if public_gateway_url and str(public_gateway_url).strip():
        return f"{str(public_gateway_url).strip().rstrip('/')}/vk/oauth/callback"
    explicit = (settings.VK_OAUTH_REDIRECT_URI or "").strip()
    if explicit:
        return explicit
    base = (settings.VK_PUBLIC_GATEWAY_URL or "").strip().rstrip("/")
    if not base:
        base = "http://localhost:8000"
    return f"{base}/vk/oauth/callback"
