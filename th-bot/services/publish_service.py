"""Публикация поста в Threads через Meta Graph API."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

THREADS_GRAPH_BASE = "https://graph.facebook.com/v18.0"


async def publish_text_post(threads_user_id: str, access_token: str, text: str) -> Optional[dict]:
    """
    Публикует текстовый пост в Threads.
    POST /{threads-user-id}/threads с media_type=TEXT.
    """
    url = f"{THREADS_GRAPH_BASE}/{threads_user_id}/threads"
    params = {"access_token": access_token}
    payload = {
        "media_type": "TEXT",
        "text": text[:500],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Threads API publish failed: %s", e)
            return None


async def publish_image_post(
    threads_user_id: str,
    access_token: str,
    text: str,
    image_url: str,
) -> Optional[dict]:
    """
    Публикует пост с изображением. image_url должен быть публично доступен.
    """
    url = f"{THREADS_GRAPH_BASE}/{threads_user_id}/threads"
    params = {"access_token": access_token}
    payload = {
        "media_type": "IMAGE",
        "text": text[:500] if text else "",
        "image_url": image_url,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning("Threads API publish image failed: %s", e)
            return None
