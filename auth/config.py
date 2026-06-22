from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения."""
    
    # Database
    DATABASE_URL: str = 'dbname=db_bot user=postgres password=1qaz!QAZ host=host.docker.internal' #127.0.0.1 - для локального запуска, host.docker.internal для локального запуска из докера #postgresql://localhost:5432/postgres'


    # JWT Settings
    SECRET_KEY: str = "$2b$12$xyiAcpacCfrFN3wl3ayJT."
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email Verification Token Expiry (in hours)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # Password Reset Token Expiry (in hours)
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # Stripe (опционально; без STRIPE_WEBHOOK_SECRET вебхук отклоняется)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_BASIC: str = ""
    STRIPE_PRICE_PREMIUM: str = ""
    BILLING_PORTAL_RETURN_URL: str = "http://localhost:5173/profile?tab=billing"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

