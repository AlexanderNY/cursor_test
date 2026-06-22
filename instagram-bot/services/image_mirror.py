"""Копирование URL картинок из сбора в S3/MinIO (как у загрузок из UI)."""

import json
import logging
from pathlib import Path
from typing import Any, List
from urllib.parse import urlparse

import httpx

from config import settings
from database import get_db_connection, release_db_connection
from storage_helper import get_storage

logger = logging.getLogger(__name__)

S3_KEY_PREFIX = "uploads/instagram/collected"


def _ext_from_url_or_ct(url: str, content_type: str | None) -> str:
    if content_type:
        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        if "png" in content_type:
            return ".png"
        if "webp" in content_type:
            return ".webp"
        if "gif" in content_type:
            return ".gif"
    path = urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return ext if ext != ".jpeg" else ".jpg"
    return ".jpg"


async def mirror_collected_images_to_storage(
    post_id: int,
    user_id: int,
    image_urls: List[str],
) -> None:
    """Скачивает внешние URL и сохраняет в bucket; обновляет instagram_posts.images путями /uploads/instagram/..."""
    if not getattr(settings, "COLLECT_MIRROR_IMAGES_TO_S3", True):
        return
    storage = get_storage()
    if not storage:
        return
    if not image_urls:
        return

    new_paths: List[str] = []
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for idx, url in enumerate(image_urls):
            if not url or not isinstance(url, str):
                continue
            u = url.strip()
            if u.startswith("/uploads/"):
                new_paths.append(u)
                continue
            if not u.lower().startswith(("http://", "https://")):
                new_paths.append(u)
                continue
            try:
                resp = await client.get(u)
                resp.raise_for_status()
                body = resp.content
                ct = resp.headers.get("content-type")
                ext = _ext_from_url_or_ct(u, ct)
                key = f"{S3_KEY_PREFIX}/{user_id}/{post_id}_{idx}{ext}"
                await storage.put(key, body)
                rel = f"/uploads/instagram/collected/{user_id}/{post_id}_{idx}{ext}"
                new_paths.append(rel)
            except Exception as e:
                logger.warning("mirror image failed post_id=%s url=%s: %s", post_id, u[:80], e)
                new_paths.append(u)

    if not new_paths:
        return

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE instagram_posts
                SET images = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (json.dumps(new_paths), post_id),
            )
    finally:
        await release_db_connection(conn)
