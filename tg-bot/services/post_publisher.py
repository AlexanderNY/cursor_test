"""Публикация постов со статусом ready в channel_to_post."""

import asyncio
import json
import logging
import os
import tempfile
from typing import Dict, List, Optional
import httpx
from database import get_db_connection, release_db_connection
from config import settings
from storage_helper import get_storage
from .client_manager import TelegramClientManager


logger = logging.getLogger(__name__)

TG_MESSAGE_LIMIT = 4096


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class PostPublisher:
    """Сервис публикации постов из tg_posts в Telegram канал."""

    def __init__(self, client_manager: TelegramClientManager):
        self.client_manager = client_manager

    async def get_ready_posts(self) -> List[Dict]:
        """Получает посты со статусом ready с channel_to_post из tg_profiles."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.user_id, p.post_text, p.images, p.status,
                           pr.channel_to_post
                    FROM tg_posts p
                    JOIN tg_profiles pr ON p.user_id = pr.user_id
                    WHERE p.status = 'ready'
                      AND pr.channel_to_post IS NOT NULL
                      AND pr.channel_to_post != ''
                    ORDER BY p.created_at ASC
                    """
                )
                rows = await cur.fetchall()
                columns = [col.name for col in cur.description]
                result = [dict(zip(columns, row)) for row in rows]
                if len(result) == 0:
                    await cur.execute(
                        "SELECT COUNT(*) FROM tg_posts WHERE status = 'ready'"
                    )
                    (ready_count,) = (await cur.fetchone()) or (0,)
                    await cur.execute(
                        """
                        SELECT COUNT(*) FROM tg_profiles
                        WHERE channel_to_post IS NOT NULL AND channel_to_post != ''
                        """
                    )
                    (profiles_with_channel,) = (await cur.fetchone()) or (0,)
                    logger.info(
                        "get_ready_posts returned 0 posts; "
                        "tg_posts with status=ready: %s, "
                        "tg_profiles with channel_to_post set: %s",
                        ready_count,
                        profiles_with_channel,
                    )
                return result
        finally:
            await release_db_connection(conn)

    def _resolve_image_path(self, image_path: str) -> Optional[str]:
        """Преобразует относительный путь изображения в абсолютный (только локальные пути)."""
        if not image_path or not isinstance(image_path, str):
            return None
        image_path = image_path.strip()
        if not image_path:
            return None
        # Уже абсолютный путь к существующему файлу
        if os.path.isabs(image_path) and os.path.exists(image_path):
            return os.path.abspath(image_path)
        # Относительный путь: base + path без ведущего /
        path = image_path.lstrip("/")
        base = (settings.PATH_TO_TG_IMAGE or os.getcwd()).rstrip("/")
        full_path = os.path.join(base, path) if path else os.path.join(base, image_path)
        if os.path.exists(full_path):
            return os.path.abspath(full_path)
        if os.path.exists(image_path):
            return os.path.abspath(image_path)
        logger.debug(
            "Image file not found: tried %s and %s (base=%s)",
            full_path,
            image_path,
            base,
        )
        return None

    def _get_first_image_ref(self, images_raw) -> Optional[str]:
        """Извлекает первый путь или URL изображения из images (JSONB / list / dict)."""
        if images_raw is None:
            return None
        try:
            images = json.loads(images_raw) if isinstance(images_raw, str) else images_raw
            if isinstance(images, list) and images:
                first = images[0]
                if isinstance(first, str):
                    return first.strip() or None
                if isinstance(first, dict):
                    return (first.get("path") or first.get("url")) or None
                return str(first).strip() or None
        except (json.JSONDecodeError, TypeError):
            logger.debug("Failed to parse images for post: %s", type(images_raw))
        return None

    async def _download_image_url(self, url: str) -> Optional[str]:
        """Скачивает изображение по URL во временный файл. Возвращает путь к файлу или None."""
        if not url or not url.strip().lower().startswith(("http://", "https://")):
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                suffix = ".jpg"
                if "content-type" in resp.headers:
                    ct = (resp.headers.get("content-type") or "").lower()
                    if "png" in ct:
                        suffix = ".png"
                    elif "gif" in ct:
                        suffix = ".gif"
                    elif "webp" in ct:
                        suffix = ".webp"
                f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                f.write(resp.content)
                f.close()
                return f.name
        except Exception as e:
            logger.warning("Failed to download image from URL %s: %s", url[:80], e)
        return None

    async def resolve_image_for_publish(self, post_id: int, images_raw) -> Optional[str]:
        """
        Возвращает путь к файлу изображения: S3, URL или локальный диск.
        При отсутствии/ошибке логирует причину и возвращает None.
        """
        ref = self._get_first_image_ref(images_raw)
        if not ref:
            logger.info(
                "Post id=%s: no image attached (images=%s)",
                post_id,
                str(images_raw)[:200] if images_raw is not None else "null",
            )
            return None
        s = ref.strip()
        if s.lower().startswith(("http://", "https://")):
            local_path = await self._download_image_url(ref)
            if local_path:
                return local_path
            logger.warning("Post id=%s: could not download image URL", post_id)
            return None
        # Единое хранилище (S3): ключ = путь без ведущего /
        storage = get_storage()
        if storage:
            key = s.lstrip("/")
            if key:
                body = await storage.get_bytes(key)
                if body:
                    suffix = ".jpg"
                    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    f.write(body)
                    f.close()
                    return f.name
        local_path = self._resolve_image_path(ref)
        if not local_path:
            logger.warning(
                "Post id=%s: image file not found for ref=%s (PATH_TO_TG_IMAGE=%s, cwd=%s)",
                post_id,
                ref[:120],
                settings.PATH_TO_TG_IMAGE or "(not set)",
                os.getcwd(),
            )
        return local_path

    def _parse_channel_to_post(self, channel: str):
        """Преобразует channel_to_post в формат для send_message."""
        if not channel:
            return None
        channel = str(channel).strip()
        if channel.startswith("@"):
            return channel
        try:
            return int(channel)
        except ValueError:
            return channel

    async def publish_post(self, post: Dict) -> bool:
        """Публикует один пост в канал.

        Args:
            post: Словарь с данными поста (id, user_id, post_text, images, channel_to_post)

        Returns:
            True при успешной публикации, False иначе
        """
        post_id = post.get("id")
        user_id = post.get("user_id")
        text = post.get("post_text") or ""
        channel = self._parse_channel_to_post(post.get("channel_to_post"))

        if not channel:
            logger.warning(f"Post {post_id}: channel_to_post is empty for user {user_id}")
            return False

        client = self.client_manager.get_client(user_id)
        if not client:
            logger.warning(f"Post {post_id}: no active client for user {user_id}")
            return False

        image_path = await self.resolve_image_for_publish(post_id, post.get("images"))

        try:
            if len(text) >= TG_MESSAGE_LIMIT:
                text = text[: TG_MESSAGE_LIMIT - 3] + "..."
                image_path = None

            if image_path:
                await client.send_message(channel, text, file=image_path)
                if image_path.startswith(tempfile.gettempdir()):
                    try:
                        os.unlink(image_path)
                    except OSError:
                        pass
            else:
                await client.send_message(channel, text)

            await self._update_post_status(post_id, "published")
            _log_action("Published post %s to %s for user %s", post_id, channel, user_id)
            return True

        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}", exc_info=True)
            return False

    async def _update_post_status(self, post_id: int, status: str) -> None:
        """Обновляет статус поста в tg_posts."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tg_posts
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def publish_ready_posts(self) -> int:
        """Публикует все посты со статусом ready.

        Returns:
            Количество успешно опубликованных постов
        """
        posts = await self.get_ready_posts()
        _log_action("get_ready_posts returned %d posts", len(posts))
        if not posts:
            return 0

        published = 0
        for post in posts:
            if await self.publish_post(post):
                published += 1
            await asyncio.sleep(20)

        _log_action("publish_ready_posts: published %d of %d", published, len(posts))
        return published
