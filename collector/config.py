"""Конфигурация Collector сервиса из переменных окружения."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки Collector."""

    # База данных
    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"

    # Интервалы выполнения (секунды)
    COLLECT_INTERVAL_SEC: int = 60
    DISTRIBUTE_INTERVAL_SEC: int = 60
    DZEN_RSS_READ_INTERVAL_SEC: int = 300  # вычитка RSS из channels_to_read

    # Размер батча за один цикл
    COLLECT_BATCH_SIZE: int = 100
    DISTRIBUTE_BATCH_SIZE: int = 100

    # Порт для FastAPI сервера
    API_PORT: int = 8009

    # Уровень логирования
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Реестр исходных таблиц (платформа -> имя таблицы)
# Для добавления новой платформы достаточно добавить одну запись.
SOURCE_TABLES = [
    {"platform": "tg", "table": "tg_posts"},
    {"platform": "wp", "table": "wp_posts"},
    {"platform": "url", "table": "url_posts"},
    {"platform": "vk", "table": "vk_posts"},
    {"platform": "tw", "table": "tw_posts"},
    {"platform": "threads", "table": "threads_posts"},
    {"platform": "instagram", "table": "instagram_posts"},
    {"platform": "dzen", "table": "dzen_posts"},
    {"platform": "cpost", "table": "cpost_posts"},
]

# Колонки в админке «Platform tables»: все типичные статусы строк в *_posts; редкие из БД добавляются справа.
PLATFORM_POST_STATUSES_ORDERED = [
    "collected",
    "created",
    "processing",
    "ready",
    "review",
    "published",
    "failed",
    "skipped",
]

# Описания функций для админки (id, name_ru, description)
COLLECTOR_FUNCTIONS_FOR_ADMIN = [
    {
        "id": "collect_posts",
        "name_ru": "Запуск сбора постов для сервисов",
        "description": "Периодический сбор постов из платформенных таблиц (tg_posts, wp_posts, url_posts, vk_posts, tw_posts, threads_posts, instagram_posts, dzen_posts, cpost_posts) в центральную таблицу posts. Посты со статусом «collected» переносятся для дальнейшей обработки процессором.",
    },
    {
        "id": "distribute_posts",
        "name_ru": "Распределение готовых постов по платформам",
        "description": "Перенос постов со статусом ready из центральной таблицы posts в платформенные таблицы (tg_posts, wp_posts, vk_posts) согласно флагам to_tg, to_wp, to_vk для публикации ботами.",
    },
]

# Маппинг флагов to_* -> целевые таблицы
TARGET_TABLES = {
    "to_tg": {"platform": "tg", "table": "tg_posts"},
    "to_wp": {"platform": "wp", "table": "wp_posts"},
    "to_vk": {"platform": "vk", "table": "vk_posts"},
    "to_dzen": {"platform": "dzen", "table": "dzen_posts"},
    "to_instagram": {"platform": "instagram", "table": "instagram_posts"},
    "to_tw": {"platform": "tw", "table": "tw_posts"},
}
