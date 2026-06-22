from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database import init_db, close_db
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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчики событий жизненного цикла приложения."""
    # Startup
    await init_db(ALL_TABLES)
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Core Service",
    description="Микросервис управления профилями и постами социальных сетей",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: QuotaExceededError) -> JSONResponse:
    return JSONResponse(
        status_code=402,
        content={
            "detail": "Monthly post quota exceeded for your plan",
            "resource": exc.resource,
            "limit": exc.limit,
            "used": exc.used,
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
