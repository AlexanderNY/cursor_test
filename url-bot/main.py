"""Главный файл url-bot сервиса."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.run import router as run_router
from routers.schedule import router as schedule_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="URL Bot Service",
    description="Сервис скрапинга по URL и XPath, скриншот элемента",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(run_router)
app.include_router(schedule_router)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "URL Bot Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    from datetime import datetime
    return {"status": "healthy", "service": "url-bot", "server_time": datetime.utcnow().isoformat() + "Z"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
    )
