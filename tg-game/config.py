"""Конфигурация сервиса игрового Telegram-бота."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""

    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8015

    # Игровой бот (Bot API, aiogram). Пустой токен — polling не запускается.
    GAME_BOT_TOKEN: str = "6951168264:AAGaXyK4Bi3jiyZHm8yiN4LI6cg2UZ0pPV0"
    # Telegram user id админов (через запятую) — is_admin в game_players при /start.
    GAME_ADMIN_TELEGRAM_IDS: str = "426287794"
    # Секрет для HTTP-админки CRUD (заголовок X-Game-Admin-Token).
    GAME_ADMIN_API_TOKEN: str = "122"

    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False

    GAME_MEDIA_S3_PREFIX: str = "uploads/game"
    # Публичная база URL для image_url (внешний адрес, доступный Telegram).
    GAME_MEDIA_PUBLIC_BASE_URL: str = "https://www.copyparse.ru"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
