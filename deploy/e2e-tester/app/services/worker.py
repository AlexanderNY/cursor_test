from __future__ import annotations

import asyncio
import json
import logging

from app.config import get_settings
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


def _parse_meta(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


async def _resolve_base_url(run_row: dict, scenario_row: dict, site_row: dict | None) -> str:
    settings = get_settings()
    if run_row.get("base_url_snapshot"):
        # may already be set at create time; prefer it
        snap = str(run_row["base_url_snapshot"]).strip()
        if snap:
            return snap.rstrip("/")
    if site_row and site_row.get("base_url"):
        return str(site_row["base_url"]).rstrip("/")
    # scenario source may embed base_url — runner also reads doc; env fallback here
    return settings.TARGET_UI_URL.rstrip("/")


async def _process_one(run_id: int) -> None:
    run_row = await fetch_one("SELECT * FROM runs WHERE id = %s", (run_id,))
    if run_row is None:
        logger.error("run %s not found", run_id)
        return

    scenario_row = await fetch_one(
        "SELECT * FROM scenarios WHERE id = %s",
        (run_row["scenario_id"],),
    )
    if scenario_row is None:
        logger.error("scenario for run %s not found", run_id)
        return

    site_id = run_row.get("site_id") or scenario_row.get("site_id")
    site_row = None
    if site_id:
        site_row = await fetch_one("SELECT * FROM sites WHERE id = %s", (site_id,))

    # If create_run stored a snapshot, use it; else resolve now and keep env/site order
    base_url = await _resolve_base_url(run_row, scenario_row, site_row)

    # Prefer scenario document base_url when no explicit run/site override was stored
    # (handled inside create_run for snapshot; here only env/site)

    cred_id = run_row.get("credentials_id") or scenario_row.get("credentials_id")
    credentials_row = None
    if cred_id:
        credentials_row = await fetch_one("SELECT * FROM credentials WHERE id = %s", (cred_id,))

    scenario = {
        "id": scenario_row["id"],
        "name": scenario_row["name"],
        "format": scenario_row["format"],
        "source": scenario_row["source"],
        "credentials_id": scenario_row.get("credentials_id"),
        "site_id": scenario_row.get("site_id"),
    }
    site_meta = _parse_meta(site_row.get("meta") if site_row else None)
    await execute_run(
        run_id,
        scenario,
        credentials_row,
        base_url=base_url,
        site_meta=site_meta,
    )


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
