"""Публикация постов из instagram_posts со статусом ready в Instagram."""

import asyncio
import json
import logging
import os
import tempfile
from itertools import groupby
from typing import Any, Dict, List, Optional

import httpx
from database import get_db_connection, release_db_connection
from config import settings
from storage_helper import get_storage
from .instagram_client import InstagramClient


logger = logging.getLogger(__name__)

INSTAGRAM_CAPTION_LIMIT = 2200


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _normalize_session(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _parse_images_raw(raw: Any) -> List[str]:
    """Разбирает images (JSONB) в список путей/URL."""
    if raw is None:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(item.strip())
        elif isinstance(item, dict):
            path = item.get("path") or item.get("url") or ""
            if path:
                result.append(str(path).strip())
    return result


def _resolve_path(path_or_url: str, base_dir: str) -> Optional[str]:
    """Преобразует относительный путь в абсолютный. Для URL возвращает None."""
    if not path_or_url or not isinstance(path_or_url, str):
        return None
    path_or_url = path_or_url.strip()
    if path_or_url.lower().startswith(("http://", "https://")):
        return None
    if os.path.isabs(path_or_url) and os.path.exists(path_or_url):
        return os.path.abspath(path_or_url)
    path = path_or_url.lstrip("/")
    base = (base_dir or os.getcwd()).rstrip("/")
    full = os.path.join(base, path) if path else os.path.join(base, path_or_url)
    if os.path.exists(full):
        return os.path.abspath(full)
    if os.path.exists(path_or_url):
        return os.path.abspath(path_or_url)
    return None


async def _download_to_temp(url: str, suffix: str = ".jpg") -> Optional[str]:
    """Скачивает файл по URL во временный файл."""
    if not url or not url.strip().lower().startswith(("http://", "https://")):
        return None
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            f.write(resp.content)
            f.close()
            return f.name
    except Exception as e:
        logger.warning("Download failed %s: %s", url[:80], e)
        return None


class PostPublisher:
    """Публикация постов из instagram_posts в Instagram."""

    async def get_ready_posts(self) -> List[Dict]:
        """Посты со статусом ready и профиль с publish_enabled и учётными данными."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.user_id, p.post_text, p.images,
                           pr.username, pr.password,
                           pr.instagrapi_session, pr.instagram_verification_code
                    FROM instagram_posts p
                    JOIN instagram_profiles pr ON p.user_id = pr.user_id
                    WHERE p.status = 'ready'
                      AND pr.publish_enabled = TRUE
                      AND pr.username IS NOT NULL
                      AND pr.username != ''
                      AND pr.password IS NOT NULL
                      AND pr.password != ''
                    ORDER BY p.user_id ASC, p.created_at ASC
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                result = []
                for row in rows:
                    rec = dict(zip(cols, row))
                    rec["instagrapi_session"] = _normalize_session(rec.get("instagrapi_session"))
                    result.append(rec)
                return result
        finally:
            await release_db_connection(conn)

    async def _resolve_image_path(self, path_or_url: str, post_id: int) -> Optional[str]:
        """Возвращает локальный путь к файлу: S3, URL или локальный диск."""
        if not path_or_url:
            return None
        s = path_or_url.strip()
        if s.lower().startswith(("http://", "https://")):
            return await _download_to_temp(path_or_url, ".jpg")
        storage = get_storage()
        if storage:
            key = s.lstrip("/")
            if key:
                body = await storage.get_bytes(key)
                if body:
                    f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    f.write(body)
                    f.close()
                    return f.name
        base = (settings.UPLOADS_DIR or os.getcwd()).rstrip("/")
        return _resolve_path(path_or_url, base)

    async def publish_post(self, post: Dict, client: Optional[InstagramClient] = None) -> bool:
        """Публикует один пост в Instagram (фото или карусель). client — переиспользуемый после одного login."""
        post_id = post.get("id")
        user_id = post.get("user_id")
        caption = (post.get("post_text") or "")[:INSTAGRAM_CAPTION_LIMIT]
        username = (post.get("username") or "").strip()
        password = post.get("password") or ""
        if not username or not password:
            logger.warning("Post %s: missing username/password", post_id)
            return False
        own_client = client
        if own_client is None:
            own_client = InstagramClient(
                username,
                password,
                user_id=user_id,
                session_dict=post.get("instagrapi_session"),
                verification_code=post.get("instagram_verification_code"),
            )
            if not await own_client.login():
                logger.warning("Post %s: Instagram login failed", post_id)
                return False
        raw_images = post.get("images")
        paths = _parse_images_raw(raw_images)
        local_paths: List[str] = []
        temp_paths: List[str] = []
        for p in paths:
            local = await self._resolve_image_path(p, post_id)
            if local:
                local_paths.append(local)
                if local.startswith(tempfile.gettempdir()):
                    temp_paths.append(local)
        if not local_paths:
            _log_action("Post %s: no images, publishing as single text (photo_upload may fail)", post_id)
        try:
            if len(local_paths) == 0:
                logger.warning("Post %s: no valid images, skip", post_id)
                return False
            if len(local_paths) == 1:
                code = await own_client.photo_upload(local_paths[0], caption=caption)
            else:
                code = await own_client.album_upload(local_paths, caption=caption)
            if code is not None:
                _log_action("Published instagram post %s for user %s", post_id, user_id)
                await self._update_post_status(post_id, "published")
                return True
        finally:
            for p in temp_paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        return False

    async def _update_post_status(self, post_id: int, status: str) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE instagram_posts
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def publish_ready_posts(self) -> int:
        """Публикует посты со статусом ready: один login на user_id."""
        posts = await self.get_ready_posts()
        _log_action("get_ready_posts returned %d posts", len(posts))
        if not posts:
            return 0
        published = 0
        for user_id, group_iter in groupby(posts, key=lambda r: r["user_id"]):
            group = list(group_iter)
            first = group[0]
            username = (first.get("username") or "").strip()
            password = first.get("password") or ""
            shared_client = InstagramClient(
                username,
                password,
                user_id=user_id,
                session_dict=first.get("instagrapi_session"),
                verification_code=first.get("instagram_verification_code"),
            )
            if not await shared_client.login():
                logger.warning("Instagram login failed for user_id=%s, skipping %d posts", user_id, len(group))
                continue
            for post in group:
                if await self.publish_post(post, client=shared_client):
                    published += 1
                await asyncio.sleep(3)
        _log_action("publish_ready_posts: published %d of %d", published, len(posts))
        return published
