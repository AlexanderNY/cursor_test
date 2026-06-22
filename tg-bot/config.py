"""Конфигурация Telegram Bot сервиса."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация из переменных окружения."""
    
    # База данных
    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"
    
    # Путь для сохранения изображений
    UPLOADS_DIR: str = "uploads/tg"
    
    # Настройки логирования
    LOG_LEVEL: str = "DEBUG"
    LOG_BOT_ACTIONS: bool = True  # При True логировать все действия бота для диагностики
    
    # URL core-service для уведомлений
    CORE_SERVICE_URL: str = "http://localhost:8002"
    
    # Порт для FastAPI сервера
    API_PORT: int = 8004

    # Интервал проверки постов ready для публикации (секунды)
    PUBLISH_INTERVAL_SEC: int = 60

    # Интервал перезагрузки профилей из БД (секунды, 0 = отключено)
    RELOAD_PROFILES_INTERVAL_SEC: int = 300

    # Максимум одновременных клиентов при запуске (0 = без ограничения)
    MAX_CONCURRENT_CLIENTS: int = 20

    # Задержка между батчами клиентов при запуске (секунды)
    CLIENT_BATCH_DELAY_SEC: float = 2.0

    # Размер батча клиентов при запуске
    CLIENT_BATCH_SIZE: int = 10

    # Базовый путь для изображений (для send_message file=)
    PATH_TO_TG_IMAGE: str = ""

    # S3-совместимое хранилище (единое с core).
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = "uploads"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_USE_SSL: bool = False

    # Игровой бот (Bot API, aiogram). Пустой токен — polling не запускается.
    GAME_BOT_TOKEN: str = ""
    # Telegram user id админов (через запятую) — is_admin в game_players при /start.
    GAME_ADMIN_TELEGRAM_IDS: str = ""
    # Секрет для HTTP-админки CRUD (заголовок X-Game-Admin-Token).
    GAME_ADMIN_API_TOKEN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
