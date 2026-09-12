"""Конфигурация Collector: RSS Дзена и метрики очереди (ETL collect/distribute убраны)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки Collector."""

    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 2
    DB_POOL_MAXSIZE: int = 16

    DZEN_RSS_READ_INTERVAL_SEC: int = 300
    PROCESSOR_SERVICE_URL: str = "http://processor:8010"
    API_PORT: int = 8009
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


PLATFORM_POST_STATUSES_ORDERED = [
    "pending",
    "ready",
    "publishing",
    "published",
    "failed",
    "skipped",
    "review",
    "collected",
    "created",
    "processing",
    "deleted",
]

COLLECTOR_FUNCTIONS_FOR_ADMIN = [
    {
        "id": "wake_processor",
        "name_ru": "Разбудить processor",
        "description": "Входящие посты уже в posts. Кнопка будит processor (очередь collected).",
    },
    {
        "id": "dzen_rss",
        "name_ru": "Вычитка RSS Дзен",
        "description": "Сбор внешних RSS из dzen_profiles.channels_to_read в posts.",
    },
]
