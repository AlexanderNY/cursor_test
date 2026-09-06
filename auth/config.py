from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения."""
    
    # Database (обязательно через env / .env)
    DATABASE_URL: str = ""
    DB_POOL_MINSIZE: int = 2
    DB_POOL_MAXSIZE: int = 20

    # JWT Settings (обязательно через env / .env; должен совпадать с JWT_SECRET_KEY gateway/core)
    SECRET_KEY: str = ""
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
    # Price IDs: STANDARD/FULL preferred; BASIC/PREMIUM — legacy aliases
    STRIPE_PRICE_STANDARD: str = ""
    STRIPE_PRICE_FULL: str = ""
    STRIPE_PRICE_BASIC: str = ""
    STRIPE_PRICE_PREMIUM: str = ""
    # Reserved for future usage-based billing (not wired in v1)
    STRIPE_METERED_AI_PRICE_ID: str = ""
    STRIPE_METERED_POSTS_PRICE_ID: str = ""
    BILLING_PORTAL_RETURN_URL: str = "http://localhost:5173/profile?tab=billing"
    BILLING_CHECKOUT_SUCCESS_URL: str = "http://localhost:5173/profile?tab=billing&checkout=success"
    BILLING_CHECKOUT_CANCEL_URL: str = "http://localhost:5173/profile?tab=billing&checkout=cancel"

    # Invoice email (optional). Without SMTP, invoice is stored and returned as preview.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_STARTTLS: bool = True
    BILLING_INVOICE_SELLER: str = "CopyParse"
    BILLING_PAYMENT_INSTRUCTIONS: str = ""
    FRONTEND_URL: str = "http://localhost:8100"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def validate_required_secrets() -> None:
    """Fail-fast, если критичные секреты не заданы через окружение."""
    missing: list[str] = []
    if not (settings.DATABASE_URL or "").strip():
        missing.append("DATABASE_URL")
    if not (settings.SECRET_KEY or "").strip():
        missing.append("SECRET_KEY")
    if missing:
        raise RuntimeError(
            "Missing required secrets (set via .env or environment): "
            + ", ".join(missing)
        )


validate_required_secrets()

