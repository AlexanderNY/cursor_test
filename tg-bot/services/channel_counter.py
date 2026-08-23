"""Bump SMM channel counters via Core internal API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


async def bump_channel_counter(
    user_id: int,
    *,
    channel_id: Optional[int] = None,
    network: Optional[str] = None,
    external_id: Optional[str] = None,
    sent: int = 0,
    received: int = 0,
    failed: int = 0,
    alerts_sent: int = 0,
    direction: Optional[str] = None,
    platform: Optional[str] = None,
    post_id: Optional[int] = None,
    external_msg_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    if not channel_id and not (network and external_id):
        return
    payload: dict[str, Any] = {
        "user_id": user_id,
        "sent": sent,
        "received": received,
        "failed": failed,
        "alerts_sent": alerts_sent,
    }
    if channel_id is not None:
        payload["channel_id"] = channel_id
    if network:
        payload["network"] = network
    if external_id:
        payload["external_id"] = str(external_id)
    if direction:
        payload["direction"] = direction
    if platform:
        payload["platform"] = platform
    if post_id is not None:
        payload["post_id"] = post_id
    if external_msg_id is not None:
        payload["external_msg_id"] = str(external_msg_id)
    if metadata:
        payload["metadata"] = metadata
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{base}/internal/smm/channel-counter/bump", json=payload)
            if resp.status_code >= 400:
                logger.debug("channel counter bump HTTP %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.debug("channel counter bump failed: %s", exc)


async def record_post_metric_snapshot(
    user_id: int,
    post_id: int,
    *,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    reposts: int = 0,
) -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{base}/internal/smm/post-metrics/snapshot",
                json={
                    "user_id": user_id,
                    "platform": "tg",
                    "post_id": post_id,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "reposts": reposts,
                },
            )
    except Exception as exc:
        logger.debug("post metric snapshot failed: %s", exc)


async def record_subscriber_snapshot(channel_id: int, subscribers: int) -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base or not channel_id:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{base}/internal/smm/channel-metrics/subscribers",
                json={"channel_id": channel_id, "subscribers": max(0, int(subscribers))},
            )
    except Exception as exc:
        logger.debug("subscriber snapshot failed: %s", exc)
