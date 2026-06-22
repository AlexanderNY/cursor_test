"""Точка входа Dzen Bot: FastAPI и фоновые циклы Selenium."""

import asyncio
import logging
import signal
import sys

import uvicorn
from fastapi import FastAPI, Request

from config import settings
from database import init_db, close_db
from services.dzen_bot_service import DzenBotService
from services.dzen_subscriptions_probe import (
    verify_yandex_pending_diag_for_user,
    verify_yandex_push_for_user,
    verify_yandex_start_for_user,
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dzen Bot Service", version="1.0.0")

bot_service: DzenBotService | None = None
_reload_task: asyncio.Task | None = None


@app.get("/health")
async def health_check():
    from datetime import datetime

    return {
        "status": "ok",
        "service": "dzen-bot",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/dzen-bot/publish-once")
async def publish_once():
    """Один проход публикации ready-постов."""
    global bot_service
    if not bot_service:
        return {"status": "error", "message": "Bot service not initialized"}
    n = await bot_service.run_publish_once()
    return {"status": "ok", "published": n}


@app.post("/dzen-bot/collect-once")
async def collect_once():
    """Один проход сбора ссылок из студии."""
    global bot_service
    if not bot_service:
        return {"status": "error", "message": "Bot service not initialized"}
    n = await bot_service.run_collect_once()
    return {"status": "ok", "collected": n}


@app.post("/schedule")
async def schedule_from_scheduler():
    """Оповещение от scheduler: публикация и сбор в фоне."""
    global bot_service
    bs = bot_service
    if not bs:
        return {"status": "error", "message": "Bot service not initialized"}

    async def _run() -> None:
        try:
            pub = await bs.run_publish_once()
            coll = await bs.run_collect_once()
            logger.info("Schedule pass: published=%s collected=%s", pub, coll)
        except Exception as e:
            logger.exception("Dzen schedule pass failed: %s", e)

    asyncio.create_task(_run())
    return {"status": "ok", "message": "dzen-bot schedule pass started"}


def _x_user_id(request: Request) -> int | None:
    uid_hdr = request.headers.get("x-user-id") or request.headers.get("X-User-Id")
    if not uid_hdr:
        return None
    try:
        return int(uid_hdr)
    except ValueError:
        return None


@app.post("/dzen-bot/verify-yandex/start")
async def verify_yandex_start(request: Request):
    """Старт: вход через dzen.ru, при пуше — сессия до push-code."""
    user_id = _x_user_id(request)
    if user_id is None:
        return {
            "ok": False,
            "need_push_code": False,
            "subscriptions": [],
            "error": "Отсутствует или невалиден X-User-Id",
            "message": None,
            "diag_image_url": None,
        }
    return await verify_yandex_start_for_user(user_id)


@app.post("/dzen-bot/verify-yandex/push-code")
async def verify_yandex_push_code(request: Request):
    user_id = _x_user_id(request)
    if user_id is None:
        return {
            "ok": False,
            "need_push_code": True,
            "subscriptions": [],
            "error": "Отсутствует или невалиден X-User-Id",
            "message": None,
            "diag_image_url": None,
        }
    body = await request.json()
    code = (body or {}).get("code", "")
    if isinstance(code, (int, float)):
        code = str(int(code))
    if not (isinstance(code, str) and code.strip()):
        return {
            "ok": False,
            "need_push_code": True,
            "subscriptions": [],
            "error": "Передайте непустое поле code (строка).",
            "message": None,
            "diag_image_url": None,
        }
    return await verify_yandex_push_for_user(user_id, code.strip())


@app.get("/dzen-bot/verify-yandex/pending-diag")
async def verify_yandex_pending_diag(request: Request):
    """Актуальный скрин pending WebDriver (если push-code ещё выполняется или сессия жива)."""
    user_id = _x_user_id(request)
    if user_id is None:
        return {"diag_image_url": None, "error": "Отсутствует или невалиден X-User-Id"}
    return await verify_yandex_pending_diag_for_user(user_id)


@app.post("/dzen-bot/verify-yandex")
async def verify_yandex_legacy_start(request: Request):
    """Обратная совместимость: то же, что /verify-yandex/start."""
    return await verify_yandex_start(request)


async def run_api_server():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


def signal_handler(signum, frame):
    logger.info("Received signal %s, shutting down...", signum)
    sys.exit(0)


async def _reload_loop():
    interval = settings.RELOAD_PROFILES_INTERVAL_SEC
    if interval <= 0:
        return
    while True:
        await asyncio.sleep(interval)
        if bot_service and bot_service.is_running():
            try:
                await bot_service.run_collect_once()
            except Exception as e:
                logger.error("Scheduled collect error: %s", e, exc_info=True)


async def main():
    global bot_service, _reload_task
    try:
        logger.info("Initializing Dzen Bot...")
        await init_db([])
        logger.info("Database initialized")

        bot_service = DzenBotService()
        api_task = asyncio.create_task(run_api_server())
        await asyncio.sleep(0.5)
        await bot_service.start()

        if settings.RELOAD_PROFILES_INTERVAL_SEC > 0:
            _reload_task = asyncio.create_task(_reload_loop())

        logger.info("Dzen Bot is running on port %s.", settings.API_PORT)
        await api_task
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt, shutting down...")
    finally:
        if _reload_task:
            _reload_task.cancel()
            try:
                await _reload_task
            except asyncio.CancelledError:
                pass
        if bot_service:
            await bot_service.stop()
        await close_db()
        logger.info("Dzen Bot stopped")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)
