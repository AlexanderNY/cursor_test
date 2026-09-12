"""Collector: RSS Дзена и метрики posts / post_targets (без ETL *_posts)."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status

from config import settings, COLLECTOR_FUNCTIONS_FOR_ADMIN, PLATFORM_POST_STATUSES_ORDERED
from database import init_db, close_db, get_db_connection
from services.dzen_rss_reader_service import dzen_rss_reader_service
from shared.db.post_model import PUBLISH_PLATFORMS
from shared.queue_wakeup import wake_process_http
from schemas import (
    HealthResponse,
    CycleResult,
    ServiceStatus,
    LoopStatus,
    MetricsResponse,
    PlatformMetric,
    CollectorFunction,
)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _merge_platform_status_counts(raw: dict[str, int]) -> dict[str, int]:
    out: dict[str, int] = {}
    for status_name in PLATFORM_POST_STATUSES_ORDERED:
        out[status_name] = int(raw.get(status_name, 0))
    for key, value in raw.items():
        if key not in out:
            out[key] = int(value)
    return out


_dzen_rss_task: asyncio.Task | None = None
_started_at: datetime | None = None
_idle_loop = LoopStatus(last_run_at=None, total_processed=0, last_cycle_count=0)


async def _dzen_rss_loop() -> None:
    interval = getattr(settings, "DZEN_RSS_READ_INTERVAL_SEC", 300)
    while True:
        try:
            await dzen_rss_reader_service.run_dzen_rss_cycle()
        except Exception:
            logger.exception("Error in Dzen RSS reader loop")
        await asyncio.sleep(interval)


async def _check_tables_at_startup() -> None:
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                for table in ("posts", "post_targets"):
                    try:
                        await cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
                    except Exception as exc:
                        logger.critical(
                            "Collector: таблица %s недоступна (%s).",
                            table,
                            exc,
                        )
    except Exception as exc:
        logger.critical("Collector: не удалось подключиться к БД при старте: %s.", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _dzen_rss_task, _started_at

    await init_db()
    await _check_tables_at_startup()
    _started_at = datetime.utcnow()
    logger.info(
        "Collector started (Dzen RSS every %ds; collect/distribute ETL removed)",
        settings.DZEN_RSS_READ_INTERVAL_SEC,
    )
    _dzen_rss_task = asyncio.create_task(_dzen_rss_loop())
    yield
    if _dzen_rss_task:
        _dzen_rss_task.cancel()
        try:
            await _dzen_rss_task
        except asyncio.CancelledError:
            pass
    await close_db()
    logger.info("Collector stopped")


app = FastAPI(title="Collector", version="2.0.0", lifespan=lifespan)


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="running", service="collector")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service="collector",
        server_time=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/status", response_model=ServiceStatus)
async def get_status():
    rss = LoopStatus(
        last_run_at=dzen_rss_reader_service.last_run_at,
        total_processed=dzen_rss_reader_service.total_collected,
        last_cycle_count=dzen_rss_reader_service.last_cycle_collected,
    )
    return ServiceStatus(
        service="collector",
        version="2.0.0",
        collect_interval_sec=settings.DZEN_RSS_READ_INTERVAL_SEC,
        distribute_interval_sec=0,
        collect_batch_size=0,
        distribute_batch_size=0,
        collector=rss,
        distributor=_idle_loop,
        current_time=datetime.utcnow().isoformat() + "Z",
        started_at=_started_at.isoformat() + "Z" if _started_at else None,
        collect_functions=[CollectorFunction(**opt) for opt in COLLECTOR_FUNCTIONS_FOR_ADMIN],
    )


@app.post("/internal/collect-now", response_model=CycleResult)
async def collect_now():
    await wake_process_http(settings.PROCESSOR_SERVICE_URL or "")
    return CycleResult(status="success", message="Processor woken (collect ETL removed)", count=0)


@app.post("/internal/distribute-now", response_model=CycleResult)
async def distribute_now():
    return CycleResult(
        status="success",
        message="Distribute ETL removed; bots claim post_targets",
        count=0,
    )


@app.post("/collect/run", response_model=CycleResult)
async def force_collect():
    await wake_process_http(settings.PROCESSOR_SERVICE_URL or "")
    return CycleResult(status="success", message="Processor woken (collect ETL removed)", count=0)


@app.post("/distribute/run", response_model=CycleResult)
async def force_distribute():
    return CycleResult(
        status="success",
        message="Distribute ETL removed; bots claim post_targets",
        count=0,
    )


@app.post("/dzen-rss/run", response_model=CycleResult)
async def force_dzen_rss():
    try:
        count = await dzen_rss_reader_service.run_dzen_rss_cycle()
        return CycleResult(
            status="success",
            message=f"Dzen RSS read cycle completed, {count} posts collected",
            count=count,
        )
    except Exception as exc:
        logger.exception("Force Dzen RSS error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dzen RSS cycle failed: {exc}",
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    platforms: list[PlatformMetric] = []
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT platform, status, COUNT(*) AS cnt
                FROM post_targets
                GROUP BY platform, status
                """
            )
            by_platform: dict[str, dict[str, int]] = {p: {} for p in PUBLISH_PLATFORMS}
            for platform, status_name, cnt in await cur.fetchall():
                bucket = by_platform.setdefault(str(platform), {})
                label = status_name if status_name and str(status_name).strip() else "(empty)"
                bucket[label] = int(cnt)
            for platform in PUBLISH_PLATFORMS:
                status_counts = _merge_platform_status_counts(by_platform.get(platform, {}))
                platforms.append(
                    PlatformMetric(
                        platform=platform,
                        table="post_targets",
                        collected_count=status_counts.get("pending", 0),
                        created_count=0,
                        ready_count=status_counts.get("ready", 0),
                        processing_count=status_counts.get("publishing", 0),
                        status_counts=status_counts,
                    )
                )
            await cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN status = 'collected' THEN 1 ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN status = 'review' THEN 1 ELSE 0 END), 0),
                    COUNT(*)
                FROM posts
                """
            )
            posts_row = await cur.fetchone()

    return MetricsResponse(
        platforms=platforms,
        posts_table={
            "collected": posts_row[0],
            "processing": posts_row[1],
            "ready": posts_row[2],
            "review": posts_row[3],
            "total": posts_row[4],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
