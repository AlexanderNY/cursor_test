from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database import init_db, close_db
from site_database import init_site_db, close_site_db
from site_schema import SITE_ALL_TABLES, SITE_SCHEMA_PATCHES
from models import ALL_TABLES
from exceptions import QuotaExceededError
from routers import (
    healthcheck,
    statistics,
    schedules,
    telegram,
    twitter,
    wordpress,
    vkontakte,
    dzen,
    instagram,
    curl,
    cpost,
    notifications,
    feedback,
    admin,
    threads,
    internal,
    smm,
    guide,
    learn,
    site,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчики событий жизненного цикла приложения."""
    await init_db(ALL_TABLES)
    await init_site_db(SITE_ALL_TABLES + SITE_SCHEMA_PATCHES)
    yield
    await close_site_db()
    await close_db()


app = FastAPI(
    title="Core Service",
    description="Микросервис управления профилями и постами социальных сетей",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение роутеров
app.include_router(healthcheck.router)
app.include_router(statistics.router)
app.include_router(schedules.router)
app.include_router(telegram.router)
app.include_router(twitter.router)
app.include_router(wordpress.router)
app.include_router(vkontakte.router)
app.include_router(dzen.router)
app.include_router(instagram.router)
app.include_router(curl.router)
app.include_router(cpost.router)
app.include_router(notifications.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(threads.router)
app.include_router(internal.router)
app.include_router(smm.router)
app.include_router(guide.router)
app.include_router(learn.router)
app.include_router(site.router)


@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: QuotaExceededError) -> JSONResponse:
    if exc.resource == "ai_calls_month":
        message = (
            "Лимит AI-вызовов исчерпан. Обновите план, чтобы продолжить."
            if exc.limit > 0
            else "AI недоступен на текущем плане. Обновите план."
        )
    elif exc.resource.startswith("feature:"):
        feat = exc.resource.split(":", 1)[-1]
        message = f"Функция «{feat}» недоступна на текущем плане. Обновите план."
    else:
        message = f"Лимит плана исчерпан: {exc.resource} ({exc.used}/{exc.limit})"
    return JSONResponse(
        status_code=402,
        content={
            "detail": {
                "message": message,
                "resource": exc.resource,
                "limit": exc.limit,
                "used": exc.used,
                "upgrade_url": "/pricing",
            }
        },
    )


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "Core Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "service": "core",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
