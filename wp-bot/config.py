"""Конфигурация wp-bot сервиса из переменных окружения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация wp-bot сервиса."""
    
    # База данных (та же БД что и core)
    DATABASE_URL: str = "dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal"
    
    # API Gateway URL для запросов к core
    API_GATEWAY_URL: str = "http://localhost:8000"
    
    # Периодичность проверки schedule_snapshot_wp (секунды)
    POLL_INTERVAL_SECONDS: int = 120
    
    # Максимум постов за один проход сбора
    COLLECT_POSTS_LIMIT: int = 10
    
    # Максимум постов за один проход публикации
    PUBLISH_POSTS_LIMIT: int = 10
    
    # URL core сервиса для получения профилей и постов
    CORE_SERVICE_URL: str = "http://localhost:8002"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
