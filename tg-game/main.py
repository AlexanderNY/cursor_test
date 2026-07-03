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
from routers.game_menu_admin import router as game_menu_admin_router
from routers.game_orders_admin import router as game_orders_admin_router
from routers.game_bots_admin import router as game_bots_admin_router
from routers.game_media_admin import router as game_media_admin_router
from routers.game_media_public import router as game_media_public_router
from routers.game_rating import router as game_rating_router
from services.bot_manager import reload_all_bots
from services.bot_telegram import fetch_bot_info
from services.game_repository import game_repository

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def _bootstrap_bots_from_env() -> None:
    default_token = (settings.GAME_BOT_TOKEN or "").strip()
    if not default_token:
        return

    existing_id = await game_repository.find_bot_id_by_token(default_token)
    if existing_id is None:
        try:
            info = await fetch_bot_info(default_token)
        except Exception as exc:
            logger.warning("Could not validate GAME_BOT_TOKEN on bootstrap: %s", exc)
            return
        username = info.get("username")
        display_name = f"@{username}" if username else "Основной бот"
        bot_id = await game_repository.admin_create_bot(
            name=display_name,
            token=default_token,
            username=username,
            is_active=True,
        )
        logger.info("Created default game bot id=%s from GAME_BOT_TOKEN", bot_id)
        existing_id = bot_id

    await game_repository.assign_orphan_records_to_bot(existing_id)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Initializing database...")
    await init_db(GAME_TABLE_DDL)
    logger.info("Database initialized")

    await _bootstrap_bots_from_env()
    await reload_all_bots()
    logger.info("Game bots polling started.")

    yield

    from services.bot_manager import stop_all_bots

    await stop_all_bots()

    await close_db()
    logger.info("Game service stopped")


app = FastAPI(title="Telegram Game Bot Service", version="1.0.0", lifespan=lifespan)
app.include_router(game_rating_router, prefix="/tg/game")
app.include_router(game_bots_admin_router, prefix="/tg/game")
app.include_router(game_admin_router, prefix="/tg/game")
app.include_router(game_menu_admin_router, prefix="/tg/game")
app.include_router(game_orders_admin_router, prefix="/tg/game")
app.include_router(game_media_admin_router, prefix="/tg/game")
app.include_router(game_media_public_router, prefix="/tg/game")


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
