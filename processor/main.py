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
_started_at: datetime | None = None


# ── Фоновый цикл ──────────────────────────────────────────────────

async def _processor_loop() -> None:
    """Фоновый цикл обработки постов."""
    while True:
        try:
            await processing_service.run_processing_cycle()
        except Exception:
            logger.exception("Error in processor loop")
        await asyncio.sleep(settings.PROCESS_INTERVAL_SEC)


# ── Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _process_task, _started_at

    await init_db()
    _started_at = datetime.utcnow()
    logger.info(
        "Processor started; processing every %ds, batch size %d",
        settings.PROCESS_INTERVAL_SEC,
        settings.PROCESS_BATCH_SIZE,
    )

    _process_task = asyncio.create_task(_processor_loop())

    yield

    if _process_task:
        _process_task.cancel()
        try:
            await _process_task
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
                    COALESCE(SUM(CASE WHEN status = 'distributed' THEN 1 ELSE 0 END), 0),
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
            "distributed": row[4],
            "total": row[5],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
