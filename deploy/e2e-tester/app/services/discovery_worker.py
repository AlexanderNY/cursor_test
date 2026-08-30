from __future__ import annotations

import asyncio
import logging

from app.services.discovery import execute_discovery

logger = logging.getLogger(__name__)

_discovery_task: asyncio.Task | None = None
_discovery_queue: asyncio.Queue[int] | None = None


def get_discovery_queue() -> asyncio.Queue[int]:
    global _discovery_queue
    if _discovery_queue is None:
        _discovery_queue = asyncio.Queue()
    return _discovery_queue


async def enqueue_discovery(discovery_id: int) -> None:
    await get_discovery_queue().put(discovery_id)


async def _discovery_loop() -> None:
    queue = get_discovery_queue()
    logger.info("discovery worker started")
    while True:
        discovery_id = await queue.get()
        try:
            await execute_discovery(discovery_id)
        except Exception:
            logger.exception("discovery worker failed on %s", discovery_id)
        finally:
            queue.task_done()


async def start_discovery_worker() -> None:
    global _discovery_task
    get_discovery_queue()
    if _discovery_task is None or _discovery_task.done():
        _discovery_task = asyncio.create_task(_discovery_loop())


async def stop_discovery_worker() -> None:
    global _discovery_task
    if _discovery_task is not None:
        _discovery_task.cancel()
        try:
            await _discovery_task
        except asyncio.CancelledError:
            pass
        _discovery_task = None
