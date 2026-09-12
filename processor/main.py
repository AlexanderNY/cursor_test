"""Processor: обработка постов из таблицы posts (status='collected')."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status

from config import settings, PROCESSING_OPTIONS_FOR_ADMIN
from database import init_db, close_db, get_db_connection
from services.processing_service import processing_service
from shared.queue_wakeup import CHANNEL_PROCESS, WakeGate, listen_forever, wake_distribute_http
from schemas import (
    HealthResponse,
    CycleResult,
    ServiceStatus,
    LoopStatus,
    MetricsResponse,
    ProcessingOption,
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_process_task: asyncio.Task | None = None
_listen_task: asyncio.Task | None = None
_started_at: datetime | None = None
_process_gate = WakeGate()


# ── Фоновый цикл ──────────────────────────────────────────────────

async def _processor_loop() -> None:
    """Фоновый цикл обработки: drain, затем interval или LISTEN/HTTP wake."""
    while True:
        processed = 0
        try:
            processed = await processing_service.run_processing_cycle()
            if processed > 0:
                await wake_distribute_http(settings.COLLECTOR_SERVICE_URL)
                continue
        except Exception:
            logger.exception("Error in processor loop")
        await _process_gate.wait(settings.PROCESS_INTERVAL_SEC)


# ── Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _process_task, _listen_task, _started_at

    await init_db()
    _started_at = datetime.utcnow()
    logger.info(
        "Processor started; processing every %ds, batch size %d",
        settings.PROCESS_INTERVAL_SEC,
        settings.PROCESS_BATCH_SIZE,
    )

    _process_task = asyncio.create_task(_processor_loop())
    _listen_task = asyncio.create_task(
        listen_forever(settings.DATABASE_URL, CHANNEL_PROCESS, _process_gate)
    )

    yield

    for task in (_process_task, _listen_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    await close_db()
    logger.info("Processor stopped")


# ── FastAPI ─────────────────────────────────────────────────────────

app = FastAPI(title="Processor", version="1.0.0", lifespan=lifespan)


@app.get("/", response_model=HealthResponse)
async def root():
    """Корневой endpoint."""
    return HealthResponse(status="running", service="processor")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Healthcheck."""
    return HealthResponse(status="healthy", service="processor", server_time=datetime.utcnow().isoformat() + "Z")


@app.get("/status", response_model=ServiceStatus)
async def get_status():
    """Текущий статус фонового цикла обработки и конфигурация."""
    return ServiceStatus(
        service="processor",
        version="1.0.0",
        process_interval_sec=settings.PROCESS_INTERVAL_SEC,
        process_batch_size=settings.PROCESS_BATCH_SIZE,
        processor=LoopStatus(
            last_run_at=processing_service.last_run_at,
            total_processed=processing_service.total_processed,
            last_cycle_count=processing_service.last_cycle_processed,
        ),
        current_time=datetime.utcnow().isoformat() + "Z",
        started_at=_started_at.isoformat() + "Z" if _started_at else None,
        processing_options=[ProcessingOption(**opt) for opt in PROCESSING_OPTIONS_FOR_ADMIN],
    )


@app.post("/internal/process-now", response_model=CycleResult)
async def process_now():
    """Пропустить sleep process-цикла (NOTIFY/HTTP wake)."""
    _process_gate.wake()
    return CycleResult(status="success", message="Process loop woken", count=0)


@app.post("/process/run", response_model=CycleResult)
async def force_process():
    """Принудительный запуск одного цикла обработки."""
    try:
        count = await processing_service.run_processing_cycle()
        return CycleResult(
            status="success",
            message=f"Processing cycle completed, {count} posts processed",
            count=count,
        )
    except Exception as e:
        logger.exception("Force process error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing cycle failed: {e}",
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Метрики по количеству постов в таблице posts по статусам."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
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
            row = await cur.fetchone()

    return MetricsResponse(
        posts_table={
            "collected": row[0],
            "processing": row[1],
            "ready": row[2],
            "review": row[3],
            "total": row[4],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
