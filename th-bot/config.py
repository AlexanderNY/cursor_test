"""Конфигурация Threads Bot сервиса.

Режим Selenium (fallback при сбое OAuth):
- Вариант A (реализуемый): только диагностика веб-входа Meta; не выдаёт Graph API access_token
  и не заменяет OAuth для публикации в Threads API.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""

    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    LOG_LEVEL: str = "INFO"

    # Порт FastAPI
    API_PORT: int = 8009

    # Core (для опроса расписания при необходимости)
    CORE_SERVICE_URL: str = "http://localhost:8002"

    # Meta Threads OAuth
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    THREADS_OAUTH_REDIRECT_URI: str = ""
    THREADS_OAUTH_SCOPE: str = "threads_basic,threads_content_publish"

    # Selenium: резервный веб-вход (явно включать в prod)
    ENABLE_THREADS_SELENIUM_FALLBACK: bool = False
    SELENIUM_HEADLESS: bool = True
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 45
    SELENIUM_IMPLICIT_WAIT: int = 5
    META_WEB_LOGIN_URL: str = "https://www.facebook.com/login/"
    INSTAGRAM_WEB_LOGIN_URL: str = "https://www.instagram.com/"
    # Не встраивать base64-скрин в JSON, если PNG слишком велик
    SELENIUM_DIAG_BASE64_MAX_BYTES: int = 1_500_000
    THREADS_SELENIUM_RATE_LIMIT_SECONDS: int = 300

    # MinIO / S3 для диагностических скриншотов Selenium (ключи содержат подстроку diag)
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
