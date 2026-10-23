"""Threads Graph API helpers (graph.threads.net) for reading posts."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

THREADS_GRAPH = "https://graph.threads.net/v1.0"


async def fetch_user_threads(
    access_token: str,
    threads_user_id: str,
    *,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    GET /{threads-user-id}/threads — обычно свои посты (OAuth user token).
    """
    uid = str(threads_user_id or "").strip()
    token = (access_token or "").strip()
    if not uid or not token:
        return []
    url = f"{THREADS_GRAPH}/{uid}/threads"
    params = {
        "access_token": token,
        "fields": "id,text,timestamp,permalink,username,media_type",
        "limit": max(1, min(50, int(limit))),
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            if resp.status_code == 200:
                rows = data.get("data") or []
                return rows if isinstance(rows, list) else []
            logger.debug("fetch_user_threads %s -> %s %s", uid, resp.status_code, data)
    except Exception as exc:
        logger.warning("fetch_user_threads %s: %s", uid, exc)
    return []


async def lookup_profile_by_username(
    access_token: str,
    username: str,
) -> Optional[Dict[str, Any]]:
    """
    GET /profile_lookup?username=… — публичный профиль (если разрешено приложению).
    Может быть недоступен на части тарифов/permissions.
    """
    handle = (username or "").strip().lstrip("@")
    token = (access_token or "").strip()
    if not handle or not token:
        return None
    url = f"{THREADS_GRAPH}/profile_lookup"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                params={"access_token": token, "username": handle},
            )
            data = resp.json()
            if resp.status_code >= 400:
                logger.debug("profile_lookup %s -> %s %s", handle, resp.status_code, data)
                return None
            if isinstance(data, dict) and data.get("id"):
                return data
            return None
    except Exception as exc:
        logger.warning("profile_lookup %s: %s", handle, exc)
        return None


def canonical_thread_url(thread_id: str, permalink: Optional[str] = None) -> str:
    """Канонический URL поста для source_native_id."""
    if permalink and str(permalink).startswith("http"):
        return str(permalink).split("?")[0].rstrip("/")
    tid = str(thread_id or "").strip()
    return f"https://www.threads.net/t/{tid}" if tid else ""
