"""Telegram Game Bot: HTTP API + aiogram polling."""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI

from config import settings
from database import close_db, init_db
from game_schema import GAME_TABLE_DDL
from routers.game_admin import router as game_admin_router
from routers.game_rating import router as game_rating_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_game_poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _game_poll_task

    logger.info("Initializing database...")
    await init_db(GAME_TABLE_DDL)
    logger.info("Database initialized")

    game_token = (settings.GAME_BOT_TOKEN or "").strip()
    if game_token:
        from bots.game_bot_runner import run_game_bot_polling

        _game_poll_task = asyncio.create_task(run_game_bot_polling(game_token))
        logger.info("Game bot (aiogram) polling task started.")

    yield

    if _game_poll_task:
        _game_poll_task.cancel()
        try:
            await _game_poll_task
        except asyncio.CancelledError:
            pass
        _game_poll_task = None

    await close_db()
    logger.info("Game service stopped")


app = FastAPI(title="Telegram Game Bot Service", version="1.0.0", lifespan=lifespan)
app.include_router(game_rating_router, prefix="/tg/game")
app.include_router(game_admin_router, prefix="/tg/game")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "tg-game",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
