"""Threads Bot: FastAPI сервис для OAuth и публикации в Threads (Meta)."""

import logging
import sys

from fastapi import FastAPI
import uvicorn

from database import init_db, close_db
from routers import router as threads_router
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Threads Bot Service", version="1.0.0")
app.include_router(threads_router)


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


@app.get("/health")
async def health():
    from datetime import datetime
    return {"status": "ok", "service": "th-bot", "server_time": datetime.utcnow().isoformat() + "Z"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
