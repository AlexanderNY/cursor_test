"""Конфигурация Scheduler из config.yaml и переменных окружения."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки Scheduler."""

    API_GATEWAY_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    POLL_INTERVAL_SECONDS: int =  60
    NOTIFY_ON_CHANGE_ONLY: bool =  True

    SCHEDULER_LOGIN: Optional[str] = None
    SCHEDULER_PASSWORD: Optional[str] = None
    SCHEDULER_JWT: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Описания функций для админки (id, name_ru, description)
SCHEDULER_FUNCTIONS_FOR_ADMIN = [
    {
        "id": "schedule_collection",
        "name_ru": "Запуск сбора расписаний для сервисов",
        "description": "Периодический опрос Core (GET /core/schedules), получение профилей платформ (tg, wp, tw, vk, threads) через API Gateway, преобразование в расписания и сохранение в таблицу schedule_snapshots.",
    },
    {
        "id": "notify_bots_on_change",
        "name_ru": "Оповещение ботов при изменении расписания",
        "description": "При изменении снимка расписания оповещение ботов платформ (tg, wp, vk, url, threads) для обновления их конфигурации.",
    },
]
