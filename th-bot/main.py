"""Threads Bot: FastAPI сервис для OAuth, сбора и публикации в Threads (Meta)."""

import asyncio
import logging
import sys

from fastapi import FastAPI, Depends
import uvicorn

from database import init_db, close_db
from routers import router as threads_router
from config import settings
from shared.internal_auth_fastapi import require_internal_token

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Threads Bot Service", version="1.0.0")
app.include_router(threads_router)

_collect_task: asyncio.Task | None = None


async def _collect_loop() -> None:
    from services.feed_collector import FeedCollector

    collector = FeedCollector()
    interval = max(60, int(getattr(settings, "FEED_COLLECT_INTERVAL_SEC", 300) or 300))
    while True:
        try:
            n = await collector.run_collect()
            if n:
                logger.info("Threads collect saved %s posts", n)
        except Exception:
            logger.exception("Threads collect loop error")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def startup():
    global _collect_task
    await init_db()
    _collect_task = asyncio.create_task(_collect_loop())


@app.on_event("shutdown")
async def shutdown():
    global _collect_task
    if _collect_task:
        _collect_task.cancel()
        try:
            await _collect_task
        except asyncio.CancelledError:
            pass
        _collect_task = None
    await close_db()


@app.get("/health")
async def health():
    from datetime import datetime
    return {"status": "ok", "service": "th-bot", "server_time": datetime.utcnow().isoformat() + "Z"}


@app.post("/internal/publish-now")
async def publish_now():
    """Wake Threads publisher immediately."""
    from routers.threads import schedule

    return await schedule()


@app.post("/internal/collect-now")
async def collect_now(_internal: None = Depends(require_internal_token)):
    """One-shot brand-channel / legacy collect."""
    from services.feed_collector import FeedCollector

    n = await FeedCollector().run_collect()
    return {"status": "ok", "saved": n}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
