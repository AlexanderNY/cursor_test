"""Конфигурация сервиса игрового Telegram-бота."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""

    DATABASE_URL: str = ""

    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8015

    # Игровой бот (Bot API, aiogram). Пустой токен — polling не запускается.
    GAME_BOT_TOKEN: str = ""
    # Telegram user id админов (через запятую) — is_admin в game_players при /start.
    GAME_ADMIN_TELEGRAM_IDS: str = ""
    # Секрет для HTTP-админки CRUD (заголовок X-Game-Admin-Token).
    GAME_ADMIN_API_TOKEN: str = ""

    # S3 / MinIO для медиатеки опросов и меню.
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = True
    GAME_MEDIA_S3_PREFIX: str = "uploads/game"
    # Публичная база URL для image_url (внешний адрес API gateway, доступный Telegram).
    GAME_MEDIA_PUBLIC_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
