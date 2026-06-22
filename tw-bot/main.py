"""Точка входа tw-bot: FastAPI и фоновые циклы."""

import asyncio
import logging
import signal
import sys

import uvicorn
from fastapi import FastAPI, Request

from config import settings
from database import close_db, init_db
from services.tw_bot_service import TwBotService
from services.x_selenium_verify import verify_x_for_user

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twitter / X Bot Service", version="1.0.0")

bot_service: TwBotService | None = None


@app.get("/health")
async def health_check():
    from datetime import datetime

    return {
        "status": "ok",
        "service": "tw-bot",
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/schedule")
async def schedule_from_scheduler():
    """Оповещение от scheduler: один проход публикации и сбора ленты."""
    global bot_service
    bs = bot_service
    if not bs:
        return {"status": "error", "message": "Bot service not initialized"}

    async def _run() -> None:
        try:
            result = await bs.run_schedule_pass()
            logger.info("Schedule pass: %s", result)
        except Exception as e:
            logger.exception("Schedule pass failed: %s", e)

    asyncio.create_task(_run())
    return {"status": "ok", "message": "tw-bot schedule pass started"}


@app.post("/tw/verify-selenium")
async def tw_verify_selenium(request: Request):
    """Проверка входа X через Selenium и список following (учётные данные из БД). Требует X-User-Id."""
    uid_hdr = request.headers.get("x-user-id") or request.headers.get("X-User-Id")
    if not uid_hdr:
        return {"ok": False, "method": "selenium", "users": [], "error": "Отсутствует X-User-Id"}
    try:
        user_id = int(uid_hdr)
    except ValueError:
        return {"ok": False, "method": "selenium", "users": [], "error": "Некорректный X-User-Id"}
    return await verify_x_for_user(user_id)


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
    if bot_service:
        asyncio.create_task(bot_service.stop())
    sys.exit(0)


async def main():
    global bot_service
    try:
        logger.info("Initializing tw-bot...")
        await init_db([])
        logger.info("Database pool ready")

        bot_service = TwBotService()
        api_task = asyncio.create_task(run_api_server())
        await asyncio.sleep(0.5)
        await bot_service.start()

        logger.info("tw-bot is running on port %s", settings.API_PORT)
        await api_task
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error("Error in main: %s", e, exc_info=True)
        raise
    finally:
        if bot_service:
            await bot_service.stop()
        await close_db()
        logger.info("tw-bot stopped")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Fatal: %s", e, exc_info=True)
        sys.exit(1)
