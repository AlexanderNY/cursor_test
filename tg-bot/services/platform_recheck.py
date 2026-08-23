"""Notify Core to recheck channel auth after TG login."""

from __future__ import annotations

import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


async def notify_platform_recheck(user_id: int) -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{base}/internal/smm/platform/recheck",
                params={"user_id": user_id},
            )
    except Exception as exc:
        logger.debug("platform recheck notify failed user=%s: %s", user_id, exc)
