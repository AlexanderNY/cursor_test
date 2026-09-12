"""Wake collector/processor loops via HTTP and PostgreSQL LISTEN/NOTIFY."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aiopg
import httpx

from shared.db.post_model import NOTIFY_CHANNEL_PUBLISH

logger = logging.getLogger(__name__)

CHANNEL_COLLECT = "copyparse_collect"
CHANNEL_PROCESS = "copyparse_process"
CHANNEL_DISTRIBUTE = "copyparse_distribute"
CHANNEL_PUBLISH = NOTIFY_CHANNEL_PUBLISH
ALLOWED_CHANNELS = frozenset(
    {CHANNEL_COLLECT, CHANNEL_PROCESS, CHANNEL_DISTRIBUTE, CHANNEL_PUBLISH}
)


class WakeGate:
    """Interval wait that can be interrupted by LISTEN or HTTP."""

    def __init__(self) -> None:
        self.event = asyncio.Event()

    def wake(self) -> None:
        self.event.set()

    async def wait(self, timeout_sec: float) -> bool:
        """Wait until woken or timeout. Returns True if woken."""
        self.event.clear()
        try:
            await asyncio.wait_for(self.event.wait(), timeout=max(0.1, float(timeout_sec)))
            return True
        except TimeoutError:
            return False


async def pg_notify(cur, channel: str, payload: str = "") -> None:
    if channel not in ALLOWED_CHANNELS:
        raise ValueError(f"Unknown notify channel: {channel}")
    safe_payload = (payload or "").replace("'", "''")[:64]
    await cur.execute(f"SELECT pg_notify('{channel}', '{safe_payload}')")


async def listen_forever(
    dsn: str,
    channel: str,
    gate: WakeGate,
) -> None:
    if channel not in ALLOWED_CHANNELS:
        raise ValueError(f"Unknown listen channel: {channel}")
    while True:
        conn: Optional[aiopg.Connection] = None
        try:
            conn = await aiopg.connect(dsn)
            async with conn.cursor() as cur:
                await cur.execute(f"LISTEN {channel}")
            logger.info("LISTEN %s started", channel)
            while True:
                await conn.notifies.get()
                gate.wake()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("LISTEN %s failed; retrying", channel)
            await asyncio.sleep(5)
        finally:
            if conn is not None:
                try:
                    conn.close()
                    await conn.wait_closed()
                except Exception:
                    pass


async def wake_http(base_url: str, path: str, *, timeout: float = 5.0) -> bool:
    base = (base_url or "").rstrip("/")
    if not base:
        return False
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{base}{path}")
            return resp.status_code < 400
    except Exception as exc:
        logger.debug("wake_http %s%s failed: %s", base, path, exc)
        return False


async def wake_collect_http(collector_base_url: str, *, timeout: float = 5.0) -> bool:
    return await wake_http(collector_base_url, "/internal/collect-now", timeout=timeout)


async def wake_process_http(processor_base_url: str, *, timeout: float = 5.0) -> bool:
    return await wake_http(processor_base_url, "/internal/process-now", timeout=timeout)


async def wake_distribute_http(collector_base_url: str, *, timeout: float = 5.0) -> bool:
    return await wake_http(collector_base_url, "/internal/distribute-now", timeout=timeout)


async def wake_publish_http(bot_base_url: str, *, timeout: float = 5.0) -> bool:
    """Wake a platform bot publish loop (existing /internal/publish-now)."""
    return await wake_http(bot_base_url, "/internal/publish-now", timeout=timeout)
