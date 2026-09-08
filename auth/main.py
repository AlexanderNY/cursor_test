from datetime import datetime

from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db, close_db
from routers import profile, auth, security, groups, billing, activity
from config import settings
from shared.token_blacklist_redis import token_blacklist_redis
from services.token_service import warm_token_blacklist_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчики событий жизненного цикла приложения."""
    await init_db()
    if (settings.REDIS_URL or "").strip():
        connected = await token_blacklist_redis.connect(settings.REDIS_URL)
        if connected:
            await warm_token_blacklist_redis()
    yield
    await token_blacklist_redis.close()
    await close_db()


app = FastAPI(
    title="Auth Service",
    description="Микросервис авторизации и аутентификации",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(groups.router)
app.include_router(security.router)
app.include_router(billing.router)
app.include_router(activity.router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "Auth Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "service": "auth",
        "server_time": datetime.utcnow().isoformat() + "Z",
        "redis_blacklist": token_blacklist_redis.connected,
    }
