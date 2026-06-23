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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
