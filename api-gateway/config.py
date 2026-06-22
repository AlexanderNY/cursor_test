from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация API Gateway из переменных окружения."""
    
    # URL сервисов для маршрутизации
    AUTH_SERVICE_URL: str = "http://172.20.10.1:8001" #"http://localhost:8001"
    CORE_SERVICE_URL: str = "http://172.20.10.2:8002" #"http://localhost:8002"
    SCHEDULER_SERVICE_URL: str = "http://172.20.10.3:8003" #"http://localhost:8003"
    TG_BOT_SERVICE_URL: str = "http://172.20.10.4:8004"
    # th-bot: порт задайте через env (docker-compose часто 8013)
    THREADS_BOT_SERVICE_URL: str = "http://th-bot:8013"
    VK_BOT_SERVICE_URL: str = "http://172.20.10.5:8005"
    WP_BOT_SERVICE_URL: str = "http://172.20.10.6:8006"
    URL_BOT_SERVICE_URL: str = "http://172.20.10.7:8007"
    # dzen-bot в docker-compose: 172.20.10.13, API_PORT 8012 (не путать с th-bot :12 — это Threads)
    DZEN_BOT_SERVICE_URL: str = "http://172.20.10.13:8012"
    # tw-bot (X): внутренний порт API_PORT (по умолчанию 8011)
    TW_BOT_SERVICE_URL: str = "http://172.20.10.14:8011"
    # instagram-bot в docker-compose: сервис instagram-bot, порт 8011 (см. API_PORT). Не путать с tw-bot (.14) и th-bot (:8012).
    INSTAGRAM_BOT_SERVICE_URL: str = "http://172.20.10.11:8011"
    
    # CORS настройки (в K8s/Minikube задать через env, например через запятую)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8100,http://172.20.10.100:8100"
    CORS_ALLOWED_METHODS: list[str] = ["GET", "POST", "DELETE"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # JWT настройки
    JWT_SECRET_KEY: str = "$2b$12$xyiAcpacCfrFN3wl3ayJT."
    JWT_ALGORITHM: str = "HS256"
    
    # Rate Limiting по умолчанию
    DEFAULT_RATE_LIMIT_REQUESTS: int = 100
    DEFAULT_RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton экземпляр настроек
settings = Settings()


def get_cors_origins_list() -> list[str]:
    """Список CORS origins (парсинг из строки для env в K8s)."""
    return [x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip()]


# Rate limits по endpoints (requests per window_seconds)
RATE_LIMITS_CONFIG: dict[str, dict[str, int]] = {
    "/auth/login": {"requests": 5, "window_seconds": 60},
    "/auth/register": {"requests": 3, "window_seconds": 60},
    "/auth/reset-password": {"requests": 3, "window_seconds": 300},
    "/auth/refresh": {"requests": 10, "window_seconds": 60},
    "/auth/verify": {"requests": 5, "window_seconds": 60},
    "/core/statistics": {"requests": 30, "window_seconds": 60},
    "/core/users-statistics": {"requests": 30, "window_seconds": 60},
    "/core/schedule": {"requests": 30, "window_seconds": 60},
    "/core/start-discovery": {"requests": 10, "window_seconds": 60},
    "/core/start-bot": {"requests": 10, "window_seconds": 60},
    "/core/schedules": {"requests": 60, "window_seconds": 60},
    "/core/healthcheck": {"requests": 60, "window_seconds": 60},
    "/core/healthchecks": {"requests": 60, "window_seconds": 60},
    "/core/admin/services-status": {"requests": 60, "window_seconds": 60},
    "/core/admin/posts-tables": {"requests": 60, "window_seconds": 60},
    "/core/admin/posts": {"requests": 60, "window_seconds": 60},
    "/auth/users": {"requests": 30, "window_seconds": 60},
    "/auth/users/export": {"requests": 20, "window_seconds": 60},
    "/auth/billing/webhooks/stripe": {"requests": 200, "window_seconds": 60},
    "/wp/posts": {"requests": 30, "window_seconds": 60},
    "/wp/profile": {"requests": 30, "window_seconds": 60},
    "/wp/publish-profile": {"requests": 30, "window_seconds": 60},
    "/wp/collect-profile": {"requests": 30, "window_seconds": 60},
    "/wp/profiles": {"requests": 30, "window_seconds": 60},
    "/wp/post": {"requests": 20, "window_seconds": 60},
    "/tg/profiles": {"requests": 30, "window_seconds": 60},
    "/tw/profiles": {"requests": 30, "window_seconds": 60},
    "/vk/profiles": {"requests": 30, "window_seconds": 60},
    "/tg-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/threads/profile": {"requests": 30, "window_seconds": 60},
    "/threads/posts": {"requests": 30, "window_seconds": 60},
    "/th-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/th-bot/reload": {"requests": 20, "window_seconds": 60},
    "/wp-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/vk-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/url-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/tw-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/dzen-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/instagram-bot/schedule": {"requests": 60, "window_seconds": 60},
    "/dzen-bot/publish-once": {"requests": 30, "window_seconds": 60},
    "/dzen-bot/collect-once": {"requests": 30, "window_seconds": 60},
    "/dzen-bot/verify-yandex": {"requests": 8, "window_seconds": 60},
    "/dzen-bot/verify-yandex/start": {"requests": 8, "window_seconds": 60},
    "/dzen-bot/verify-yandex/push-code": {"requests": 12, "window_seconds": 60},
    "/tw-bot/verify-selenium": {"requests": 6, "window_seconds": 60},
    "/vk-bot/verify-selenium": {"requests": 6, "window_seconds": 60},
    "/instagram-bot/reload": {"requests": 20, "window_seconds": 60},
    "/instagram-bot/verify-code": {"requests": 10, "window_seconds": 300},
    "/instagram-bot/login-test": {"requests": 10, "window_seconds": 300},
    "/threads-bot/selenium/attempt": {"requests": 6, "window_seconds": 600},
    "/th-bot/selenium/attempt": {"requests": 6, "window_seconds": 600},
    "default": {
        "requests": settings.DEFAULT_RATE_LIMIT_REQUESTS,
        "window_seconds": settings.DEFAULT_RATE_LIMIT_WINDOW_SECONDS
    }
}


# Публичные endpoints без JWT проверки
PUBLIC_ENDPOINTS: list[str] = [
    "/threads/oauth/callback",
    "/vk/oauth/callback",
    "/dzen-bot/health",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/verify",
    "/auth/reset-password",
    "/auth/reset-password/confirm",
    "/auth/billing/plans",
    "/auth/billing/webhooks/stripe",
    "/health",
]


