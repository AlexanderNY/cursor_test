"""Конфигурация Scheduler из переменных окружения."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки Scheduler."""

    # Прямые вызовы сервисов в Docker-сети (без JWT / без SCHEDULER_LOGIN).
    # Контекст пользователя — user_id из профилей/настроек в БД.
    CORE_SERVICE_URL: str = "http://core:8002"
    API_GATEWAY_URL: str = "http://gateway:8000"  # только для admin UI proxy paths, не для poll

    TG_BOT_SERVICE_URL: str = "http://tg-bot:8004"
    WP_BOT_SERVICE_URL: str = "http://wp-bot:8006"
    VK_BOT_SERVICE_URL: str = "http://vk-bot:8005"
    TW_BOT_SERVICE_URL: str = "http://tw-bot:8011"
    URL_BOT_SERVICE_URL: str = "http://url-bot:8007"
    THREADS_BOT_SERVICE_URL: str = "http://th-bot:8013"
    DZEN_BOT_SERVICE_URL: str = "http://dzen-bot:8012"
    INSTAGRAM_BOT_SERVICE_URL: str = "http://instagram-bot:8011"

    DATABASE_URL: str = ""

    POLL_INTERVAL_SECONDS: int = 60
    NOTIFY_ON_CHANGE_ONLY: bool = True
    SMM_JOBS_RUN_ENABLED: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Описания функций для админки (id, name_ru, description)
SCHEDULER_FUNCTIONS_FOR_ADMIN = [
    {
        "id": "schedule_collection",
        "name_ru": "Запуск сбора расписаний для сервисов",
        "description": (
            "Периодический опрос Core (GET /schedules): агрегация расписаний "
            "авторизованных пользователей из БД (tg/wp/tw/vk/url/threads/…) "
            "и сохранение в schedule_snapshots."
        ),
    },
    {
        "id": "notify_bots_on_change",
        "name_ru": "Оповещение ботов при изменении расписания",
        "description": (
            "При изменении снимка расписания оповещение ботов платформ "
            "(прямые POST /schedule по user_id из БД)."
        ),
    },
]
