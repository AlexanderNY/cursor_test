"""Публикация постов из vk_posts со статусом ready на личную стену и/или в группу VK с вложениями.

Разделение клиентов VkClient: публикация на стену (wall.post) и загрузка вложений (photos/doc) могут
требовать разные типы токенов — см. docs/VK_BOT_POSTING.md.
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import httpx
from database import get_db_connection, release_db_connection
from config import settings
from storage_helper import get_storage
from .vk_client import VkClient


logger = logging.getLogger(__name__)

VK_MESSAGE_LIMIT = 16384


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _parse_group_to_post(value: Optional[str]) -> Optional[int]:
    """Преобразует group_to_post в owner_id (отрицательное число). Поддерживает числовой id и формат club123456."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # Формат "club236672543" или "236672543"
    if s.lower().startswith("club"):
        s = s[4:].strip()
    try:
        n = int(s)
        if n <= 0:
            return None
        return -n
    except ValueError:
        return None


def _parse_attachments_raw(raw: Any) -> List[Dict[str, str]]:
    """Разбирает attachments (JSONB) или images (JSONB) в список элементов с type и path/url."""
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
            result.append({"type": "photo", "path": item.strip()})
        elif isinstance(item, dict):
            t = (item.get("type") or "photo").lower()
            path = item.get("path") or item.get("url") or ""
            if path:
                result.append({"type": t, "path": path.strip()})
    return result


def _resolve_path(path_or_url: str, base_dir: str) -> Optional[str]:
    """Преобразует относительный путь в абсолютный (локальный файл). Для URL возвращает None."""
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


def _resolve_image_url(path_or_url: str) -> str:
    """Если путь относительный (/vk/uploads/...), возвращает полный URL через CORE_SERVICE_URL."""
    s = (path_or_url or "").strip()
    if not s:
        return ""
    if s.lower().startswith(("http://", "https://")):
        return s
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return s
    return f"{base}{s}" if s.startswith("/") else f"{base}/{s}"


async def _download_to_temp(url: str, suffix: str = "") -> Optional[str]:
    """Скачивает файл по URL во временный файл. Возвращает путь или None."""
    if not url or not url.strip().lower().startswith(("http://", "https://")):
        return None
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ext = suffix or ".bin"
            f = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            f.write(resp.content)
            f.close()
            return f.name
    except Exception as e:
        logger.warning("Download failed %s: %s", url[:80], e)
        return None


class PostPublisher:
    """Публикация постов из vk_posts на личную стену и/или в группу VK с вложениями (фото, документы)."""

    async def get_ready_posts(self) -> List[Dict]:
        """Посты со статусом ready и (group_to_post не пусто или post_to_own_wall = true), access_token."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.user_id, p.post_text, p.images, p.attachments,
                           pr.group_to_post, pr.access_token, pr.user_access_token, pr.from_group,
                           pr.post_to_own_wall
                    FROM vk_posts p
                    JOIN vk_profiles pr ON p.user_id = pr.user_id
                    WHERE p.status = 'ready'
                      AND (
                        (pr.access_token IS NOT NULL AND pr.access_token != '')
                        OR (pr.user_access_token IS NOT NULL AND pr.user_access_token != '')
                      )
                      AND (
                        (pr.group_to_post IS NOT NULL AND pr.group_to_post != '')
                        OR pr.post_to_own_wall = TRUE
                      )
                    ORDER BY p.created_at ASC
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        finally:
            await release_db_connection(conn)

    def _get_owner_ids(self, post: Dict, vk_user_id: Optional[int]) -> List[int]:
        """Формирует список owner_id для публикации: личная стена (если post_to_own_wall) и/или группа."""
        owner_ids: List[int] = []
        if post.get("post_to_own_wall") and vk_user_id is not None:
            owner_ids.append(vk_user_id)
        group_owner = _parse_group_to_post(post.get("group_to_post"))
        if group_owner is not None:
            owner_ids.append(group_owner)
        return owner_ids

    def _vk_client_for_wall_post(
        self,
        access_token: Optional[str],
        user_access_token: Optional[str],
        owner_id: int,
        post_id: Optional[int],
    ) -> Optional[VkClient]:
        """Клиент для wall.post: группа — community access_token; личная стена — user_access_token (предпочтительно)."""
        if owner_id < 0:
            if not access_token:
                logger.error(
                    "Post %s: wall.post to group owner_id=%s requires access_token (community)",
                    post_id,
                    owner_id,
                )
                return None
            logger.info(
                "Post %s: wall.post owner_id=%s using community access_token",
                post_id,
                owner_id,
            )
            return VkClient(access_token)
        if user_access_token:
            logger.info(
                "Post %s: wall.post owner_id=%s using user_access_token",
                post_id,
                owner_id,
            )
            return VkClient(user_access_token)
        if access_token:
            logger.warning(
                "Post %s: wall.post to personal wall without user_access_token — using access_token "
                "(must be a user token with wall scope, not a community token)",
                post_id,
            )
            return VkClient(access_token)
        logger.error("Post %s: no token for personal wall wall.post", post_id)
        return None

    def _vk_client_for_upload(
        self,
        access_token: Optional[str],
        user_access_token: Optional[str],
        owner_id: int,
        post_id: Optional[int],
    ) -> VkClient:
        """Клиент для загрузки вложений на стену. Для стены группы (owner_id < 0) photos.getWallUploadServer требует пользовательский OAuth ([27])."""
        if owner_id < 0 and user_access_token:
            logger.info(
                "Post %s: upload group wall owner_id=%s token=user",
                post_id,
                owner_id,
            )
            return VkClient(user_access_token)
        if owner_id < 0 and not user_access_token:
            logger.warning(
                "Post %s: group wall (owner_id=%s) — задайте user_access_token в vk_profiles для загрузки фото/файлов; "
                "групповой access_token не может вызывать photos.getWallUploadServer",
                post_id,
                owner_id,
            )
        if owner_id > 0 and user_access_token:
            logger.info(
                "Post %s: upload personal wall owner_id=%s token=user",
                post_id,
                owner_id,
            )
            return VkClient(user_access_token)
        fallback = access_token or user_access_token
        if not fallback:
            logger.error("Post %s: upload has no access_token or user_access_token", post_id)
            raise ValueError("VK upload requires access_token or user_access_token")
        logger.info(
            "Post %s: upload owner_id=%s token=fallback_access_or_user",
            post_id,
            owner_id,
        )
        return VkClient(fallback)

    async def _resolve_file_path(self, item: Dict[str, str], post_id: int) -> Optional[str]:
        """Возвращает локальный путь к файлу: S3 → HTTP (Core) → локальный диск. Пробует все методы последовательно."""
        path_or_url = item.get("path") or item.get("url") or ""
        if not path_or_url:
            return None
        s = path_or_url.strip()
        suffix = ".jpg" if (item.get("type") or "photo") != "doc" else ""

        if s.lower().startswith(("http://", "https://")):
            result = await _download_to_temp(s, suffix)
            if result:
                return result
            logger.warning("Post %s: HTTP download failed for %s", post_id, s[:120])
            return None

        # 1) S3
        storage = get_storage()
        if storage:
            key = s.lstrip("/")
            if key:
                try:
                    body = await storage.get_bytes(key)
                except Exception as exc:
                    logger.warning("Post %s: S3 get_bytes('%s') error: %s", post_id, key, exc)
                    body = None
                if body:
                    logger.info("Post %s: resolved '%s' from S3 (%d bytes)", post_id, key, len(body))
                    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    f.write(body)
                    f.close()
                    return f.name
                logger.info("Post %s: S3 key '%s' not found, trying HTTP fallback", post_id, key)
        else:
            logger.info("Post %s: S3 storage not configured, trying HTTP fallback", post_id)

        # 2) HTTP download via CORE_SERVICE_URL
        url = _resolve_image_url(s)
        if url and url.lower().startswith(("http://", "https://")):
            result = await _download_to_temp(url, suffix)
            if result:
                logger.info("Post %s: resolved '%s' via HTTP (%s)", post_id, s[:80], url[:120])
                return result
            logger.warning("Post %s: HTTP download failed for %s", post_id, url[:120])

        # 3) Local file
        base = (settings.PATH_TO_VK_IMAGE or settings.UPLOADS_DIR or os.getcwd()).rstrip("/")
        local = _resolve_path(s, base)
        if local:
            logger.info("Post %s: resolved '%s' from local path %s", post_id, s[:80], local)
            return local

        logger.warning("Post %s: could not resolve file '%s' (S3=%s, CORE_URL=%s)",
                        post_id, s[:120], "yes" if storage else "no", settings.CORE_SERVICE_URL)
        return None

    async def _build_attachments_string(
        self, client: VkClient, owner_id: int, post: Dict
    ) -> Optional[str]:
        """Загружает вложения поста для заданного owner_id и возвращает строку вложений для wall.post."""
        post_id = post.get("id")
        attachments_list: List[Dict] = []
        raw_attachments = post.get("attachments")
        raw_images = post.get("images")
        logger.info("Post %s: raw_attachments=%s (type=%s), raw_images=%s (type=%s)",
                     post_id,
                     str(raw_attachments)[:200], type(raw_attachments).__name__,
                     str(raw_images)[:200], type(raw_images).__name__)
        if raw_attachments:
            try:
                att = json.loads(raw_attachments) if isinstance(raw_attachments, str) else raw_attachments
                if isinstance(att, list):
                    attachments_list = _parse_attachments_raw(att)
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning("Post %s: failed to parse attachments: %s", post_id, exc)
        if not attachments_list and raw_images is not None:
            attachments_list = _parse_attachments_raw(raw_images)
        if not attachments_list:
            logger.info("Post %s: no attachments to upload", post_id)
            return None
        logger.info("Post %s: %d attachment(s) to process: %s",
                     post_id, len(attachments_list), attachments_list)
        parts: List[str] = []
        temp_paths: List[str] = []
        for idx, item in enumerate(attachments_list):
            local_path = await self._resolve_file_path(item, post_id)
            if not local_path:
                logger.warning("Post %s: could not resolve attachment #%d %s — skipping",
                               post_id, idx, item)
                continue
            if local_path.startswith(tempfile.gettempdir()):
                temp_paths.append(local_path)
            atype = (item.get("type") or "photo").lower()
            if atype == "photo":
                astr = await client.upload_photo_wall(local_path, owner_id)
            elif atype in ("doc", "document", "video", "audio"):
                astr = await client.upload_document_wall(local_path, owner_id)
            else:
                astr = await client.upload_photo_wall(local_path, owner_id)
            if astr:
                parts.append(astr)
                logger.info("Post %s: attachment #%d uploaded → %s", post_id, idx, astr)
            else:
                logger.warning("Post %s: VK upload failed for attachment #%d (path=%s, type=%s, owner_id=%s)",
                               post_id, idx, local_path, atype, owner_id)
        for p in temp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass
        result = ",".join(parts) if parts else None
        logger.info("Post %s: final attachments string: %s", post_id, result)
        return result

    async def publish_post(self, post: Dict) -> bool:
        """Публикует один пост на личную стену и/или в группу с вложениями."""
        post_id = post.get("id")
        user_id = post.get("user_id")
        text = (post.get("post_text") or "")[:VK_MESSAGE_LIMIT]
        raw_at = post.get("access_token")
        raw_uat = post.get("user_access_token")
        token = (raw_at or "").strip() or None
        user_access_token = (raw_uat or "").strip() or None
        from_group = bool(post.get("from_group", True))

        if not token and not user_access_token:
            logger.warning("Post %s: missing access_token and user_access_token", post_id)
            return False

        id_client = VkClient(user_access_token or token)
        vk_user_id: Optional[int] = None
        if post.get("post_to_own_wall"):
            vk_user_id = await id_client.get_current_user_id()
            if vk_user_id is None:
                logger.warning(
                    "Post %s: post_to_own_wall is set but get_current_user_id() failed "
                    "(set user_access_token from OAuth or use a user access_token with users scope, not only a community token)",
                    post_id,
                )

        owner_ids = self._get_owner_ids(post, vk_user_id)
        if not owner_ids:
            logger.warning(
                "Post %s: no destination — post_to_own_wall=%s (vk_user_id=%s), group_to_post=%r; "
                "set group_to_post to numeric group id and/or use user token for own wall",
                post_id,
                post.get("post_to_own_wall"),
                vk_user_id,
                post.get("group_to_post"),
            )
            return False

        published_any = False
        for owner_id in owner_ids:
            wall_client = self._vk_client_for_wall_post(
                token, user_access_token, owner_id, post_id
            )
            if wall_client is None:
                logger.warning(
                    "Post %s: skip owner_id=%s — no VkClient for wall.post",
                    post_id,
                    owner_id,
                )
                continue
            upload_client = self._vk_client_for_upload(
                token, user_access_token, owner_id, post_id
            )
            attachments_str = await self._build_attachments_string(
                upload_client, owner_id, post
            )
            new_post_id = await wall_client.wall_post(
                owner_id=owner_id,
                message=text,
                from_group=from_group and owner_id < 0,
                attachments=attachments_str,
            )
            if new_post_id is not None:
                published_any = True
                _log_action(
                    "Published vk post %s to owner_id=%s for user %s",
                    post_id,
                    owner_id,
                    user_id,
                )
            await asyncio.sleep(1)
        if published_any:
            await self._update_post_status(post_id, "published")
        return published_any

    async def _update_post_status(self, post_id: int, status: str) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE vk_posts
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def publish_ready_posts(self) -> int:
        """Публикует все посты со статусом ready. Возвращает количество опубликованных."""
        posts = await self.get_ready_posts()
        _log_action("get_ready_posts returned %d posts", len(posts))
        if not posts:
            return 0
        published = 0
        for post in posts:
            if await self.publish_post(post):
                published += 1
            await asyncio.sleep(2)
        _log_action("publish_ready_posts: published %d of %d", published, len(posts))
        return published
