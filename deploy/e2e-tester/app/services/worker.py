from __future__ import annotations

import asyncio
import logging

from app.db import fetch_one
from app.services.runner import execute_run

logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None
_queue: asyncio.Queue[int] | None = None


def get_queue() -> asyncio.Queue[int]:
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def enqueue_run(run_id: int) -> None:
    await get_queue().put(run_id)


async def _process_one(run_id: int) -> None:
    scenario_row = await fetch_one(
        """
        SELECT s.*, r.credentials_id AS run_credentials_id
        FROM runs r
        JOIN scenarios s ON s.id = r.scenario_id
        WHERE r.id = %s
        """,
        (run_id,),
    )
    if scenario_row is None:
        logger.error("run %s not found", run_id)
        return

    cred_id = scenario_row.get("run_credentials_id") or scenario_row.get("credentials_id")
    credentials_row = None
    if cred_id:
        credentials_row = await fetch_one("SELECT * FROM credentials WHERE id = %s", (cred_id,))

    scenario = {
        "id": scenario_row["id"],
        "name": scenario_row["name"],
        "format": scenario_row["format"],
        "source": scenario_row["source"],
        "credentials_id": scenario_row.get("credentials_id"),
    }
    await execute_run(run_id, scenario, credentials_row)


async def _worker_loop() -> None:
    queue = get_queue()
    logger.info("tester worker started")
    while True:
        run_id = await queue.get()
        try:
            await _process_one(run_id)
        except Exception:
            logger.exception("worker failed on run %s", run_id)
        finally:
            queue.task_done()


async def start_worker() -> None:
    global _worker_task
    get_queue()
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker_loop())


async def stop_worker() -> None:
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
