"""Helpers for bots talking to Core internal APIs (claim / snapshots / inbox).

Bots should prefer these HTTP contracts over direct Postgres for new features.
Existing publish claim loops may still touch DB until fully migrated.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


async def post_metric_snapshot(
    core_base_url: str,
    *,
    user_id: int,
    platform: str,
    post_id: int,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    reposts: int = 0,
) -> bool:
    base = (core_base_url or "").rstrip("/")
    if not base:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base}/internal/smm/post-metrics/snapshot",
                json={
                    "user_id": user_id,
                    "platform": platform,
                    "post_id": post_id,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "reposts": reposts,
                },
            )
            return resp.status_code < 400
    except Exception as exc:
        logger.debug("post_metric_snapshot failed: %s", exc)
        return False


async def claim_ready_posts(
    core_base_url: str,
    *,
    platform: str,
    limit: int = 20,
    user_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Ask Core to claim ready posts for publish (status ready -> publishing)."""
    base = (core_base_url or "").rstrip("/")
    if not base:
        return []
    payload: dict[str, Any] = {"platform": platform, "limit": limit}
    if user_id is not None:
        payload["user_id"] = user_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{base}/internal/smm/posts/claim", json=payload)
            if resp.status_code >= 400:
                logger.debug("claim_ready_posts HTTP %s: %s", resp.status_code, resp.text[:200])
                return []
            data = resp.json() if resp.content else {}
            return list(data.get("posts") or [])
    except Exception as exc:
        logger.debug("claim_ready_posts failed: %s", exc)
        return []


async def mark_post_published(
    core_base_url: str,
    *,
    platform: str,
    post_id: int,
    external_id: Optional[str] = None,
    error: Optional[str] = None,
) -> bool:
    base = (core_base_url or "").rstrip("/")
    if not base:
        return False
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{base}/internal/smm/posts/publish-result",
                json={
                    "platform": platform,
                    "post_id": post_id,
                    "external_id": external_id,
                    "error": error,
                    "ok": error is None,
                },
            )
            return resp.status_code < 400
    except Exception as exc:
        logger.debug("mark_post_published failed: %s", exc)
        return False


async def wake_publish_now(bot_base_url: str, *, timeout: float = 5.0) -> bool:
    """Ask a platform bot to drain ready posts immediately (skip poll wait)."""
    base = (bot_base_url or "").rstrip("/")
    if not base:
        return False
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{base}/internal/publish-now")
            if resp.status_code < 400:
                return True
            logger.debug(
                "wake_publish_now HTTP %s for %s: %s",
                resp.status_code,
                base,
                (resp.text or "")[:200],
            )
            return False
    except Exception as exc:
        logger.debug("wake_publish_now failed for %s: %s", base, exc)
        return False
