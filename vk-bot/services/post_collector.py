"""Сбор постов со стен групп VK и сохранение в vk_posts."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection
from config import settings
from .vk_client import VkClient


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class PostCollector:
    """Сбор постов из groups_to_read и users_to_read (стены групп и пользователей) и сохранение в vk_posts."""

    async def get_profiles_for_collect(self) -> List[Dict]:
        """Профили с collect_enabled, access_token и непустым groups_to_read или users_to_read."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, access_token, groups_to_read, users_to_read
                    FROM vk_profiles
                    WHERE collect_enabled = TRUE
                      AND access_token IS NOT NULL
                      AND access_token != ''
                      AND (
                        (groups_to_read IS NOT NULL AND jsonb_array_length(COALESCE(groups_to_read, '[]'::jsonb)) > 0)
                        OR (users_to_read IS NOT NULL AND jsonb_array_length(COALESCE(users_to_read, '[]'::jsonb)) > 0)
                      )
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                result = []
                for row in rows:
                    rec = dict(zip(cols, row))
                    if isinstance(rec.get("groups_to_read"), str):
                        try:
                            rec["groups_to_read"] = json.loads(rec["groups_to_read"])
                        except (json.JSONDecodeError, TypeError):
                            rec["groups_to_read"] = []
                    if rec.get("groups_to_read") is None:
                        rec["groups_to_read"] = []
                    if isinstance(rec.get("users_to_read"), str):
                        try:
                            rec["users_to_read"] = json.loads(rec["users_to_read"])
                        except (json.JSONDecodeError, TypeError):
                            rec["users_to_read"] = []
                    if rec.get("users_to_read") is None:
                        rec["users_to_read"] = []
                    if rec.get("groups_to_read") or rec.get("users_to_read"):
                        result.append(rec)
                return result
        finally:
            await release_db_connection(conn)

    async def get_max_source_id(self, user_id: int, domain: str) -> int:
        """Максимальный vk_source_id по user_id и domain (группа)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COALESCE(MAX(vk_source_id), 0)
                    FROM vk_posts
                    WHERE user_id = %s AND domain = %s
                    """,
                    (user_id, domain),
                )
                row = await cur.fetchone()
                return (row[0] or 0) if row else 0
        finally:
            await release_db_connection(conn)

    def _parse_group_owner_id(self, group_id: Any) -> Optional[int]:
        """Преобразует ID группы в owner_id для API (отрицательное число)."""
        if group_id is None:
            return None
        try:
            g = int(group_id)
            if g == 0:
                return None
            return -abs(g)
        except (ValueError, TypeError):
            return None

    def _parse_user_owner_id(self, user_id: Any) -> Optional[int]:
        """Преобразует ID пользователя в owner_id для API (положительное число)."""
        if user_id is None:
            return None
        try:
            u = int(user_id)
            if u <= 0:
                return None
            return u
        except (ValueError, TypeError):
            return None

    def _item_to_row(
        self,
        user_id: int,
        owner_id: int,
        item: Dict[str, Any],
    ) -> Optional[tuple]:
        """Извлекает данные поста из ответа VK API."""
        try:
            post_id = item.get("id")
            text = (item.get("text") or "")[:16384]
            ts = item.get("date")
            post_date = datetime.utcfromtimestamp(ts) if ts else None
            from_id = item.get("from_id")
            author = str(from_id) if from_id is not None else None
            if author and len(author) > 255:
                author = author[:255]
            comments = (item.get("comments") or {}).get("count", 0) or 0
            likes = (item.get("likes") or {}).get("count", 0) or 0
            reposts = (item.get("reposts") or {}).get("count", 0) or 0
            views = (item.get("views") or {}).get("count", 0) if isinstance(item.get("views"), dict) else (item.get("views") or 0)
            domain = str(owner_id)
            images = []
            for att in (item.get("attachments") or []):
                if att.get("type") == "photo":
                    photo = att.get("photo") or {}
                    # Сохраняем ссылку на фото (можно позже скачать в image_handler)
                    url = None
                    for key in ["photo_2560", "photo_1280", "photo_807", "photo_604", "photo_130"]:
                        if photo.get(key):
                            url = photo[key]
                            break
                    if url:
                        images.append(url)
            return (
                user_id,
                post_id,
                domain,
                text,
                post_date,
                author,
                json.dumps(images),
                comments,
                reposts,
                likes,
                views,
            )
        except Exception as e:
            logger.debug("_item_to_row skip item: %s", e)
            return None

    async def save_post(
        self,
        user_id: int,
        vk_source_id: int,
        domain: str,
        post_text: str,
        post_date: Optional[datetime],
        author: Optional[str],
        images_json: str,
        comments: int,
        reposts: int,
        likes: int,
        views: int,
    ) -> bool:
        """Вставляет пост в vk_posts со статусом collected (далее collector переносит в posts)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_posts (
                        user_id, vk_source_id, domain, post_text, post_date, author,
                        images, comments, reposts, likes, views,
                        status, post_type, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'collected', 'vk', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        user_id,
                        vk_source_id,
                        domain,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                    ),
                )
                _log_action(
                    "Saved vk post user_id=%s domain=%s vk_source_id=%s",
                    user_id,
                    domain,
                    vk_source_id,
                )
                return True
        except Exception as e:
            logger.error("Error saving vk post: %s", e, exc_info=True)
            return False
        finally:
            await release_db_connection(conn)

    async def run_collect(self) -> int:
        """Опрашивает стены групп и пользователей по всем профилям и сохраняет новые посты. Возвращает число сохранённых."""
        profiles = await self.get_profiles_for_collect()
        if not profiles:
            return 0
        saved = 0
        for profile in profiles:
            user_id = profile["user_id"]
            token = profile.get("access_token")
            if not token:
                continue
            groups = profile.get("groups_to_read") or []
            users = profile.get("users_to_read") or []
            client = VkClient(token)
            # Стены групп (owner_id < 0)
            for g in groups:
                owner_id = self._parse_group_owner_id(g)
                if owner_id is None:
                    continue
                domain = str(owner_id)
                max_id = await self.get_max_source_id(user_id, domain)
                items = await client.wall_get(owner_id=owner_id, count=20)
                for item in items:
                    post_id = item.get("id")
                    if post_id is None or post_id <= max_id:
                        continue
                    row = self._item_to_row(user_id, owner_id, item)
                    if not row:
                        continue
                    (
                        uid,
                        vk_source_id,
                        dom,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                    ) = row
                    ok = await self.save_post(
                        uid,
                        vk_source_id,
                        dom,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                    )
                    if ok:
                        saved += 1
            # Стены пользователей (owner_id > 0)
            for u in users:
                owner_id = self._parse_user_owner_id(u)
                if owner_id is None:
                    continue
                domain = str(owner_id)
                max_id = await self.get_max_source_id(user_id, domain)
                items = await client.wall_get(owner_id=owner_id, count=20)
                for item in items:
                    post_id = item.get("id")
                    if post_id is None or post_id <= max_id:
                        continue
                    row = self._item_to_row(user_id, owner_id, item)
                    if not row:
                        continue
                    (
                        uid,
                        vk_source_id,
                        dom,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                    ) = row
                    ok = await self.save_post(
                        uid,
                        vk_source_id,
                        dom,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                    )
                    if ok:
                        saved += 1
        return saved
