"""Главный файл wp-bot сервиса."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, close_db
from routers.schedule import router as schedule_router
from services.schedule_poll_service import poll_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Флаг для остановки фонового опроса
_poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Обработчики событий жизненного цикла приложения."""
    global _poll_task

    # Startup
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    # Запускаем фоновый опрос schedule_snapshot_wp
    _poll_task = asyncio.create_task(poll_loop())
    logger.info("Schedule poll loop started, interval=%s seconds", settings.POLL_INTERVAL_SECONDS)

    yield

    # Shutdown
    if _poll_task and not _poll_task.done():
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
        logger.info("Schedule poll loop stopped")

    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")


app = FastAPI(
    title="WordPress Bot Service",
    description="Сервис для публикации и сбора постов WordPress",
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
app.include_router(schedule_router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "WordPress Bot Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "wp-bot",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True
    )
