"""Сбор постов из Instagram (свои и usernames_to_read) и сохранение в instagram_posts."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection
from config import settings
from .image_mirror import mirror_collected_images_to_storage
from .instagram_client import InstagramClient


logger = logging.getLogger(__name__)


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


class PostCollector:
    """Сбор постов из своего аккаунта и usernames_to_read в instagram_posts."""

    async def get_profiles_for_collect(self) -> List[Dict]:
        """Профили с collect_enabled и учётными данными + сессия instagrapi."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, username, password, usernames_to_read,
                           instagrapi_session, instagram_verification_code
                    FROM instagram_profiles
                    WHERE collect_enabled = TRUE
                      AND username IS NOT NULL
                      AND username != ''
                      AND password IS NOT NULL
                      AND password != ''
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                result = []
                for row in rows:
                    rec = dict(zip(cols, row))
                    if isinstance(rec.get("usernames_to_read"), str):
                        try:
                            rec["usernames_to_read"] = json.loads(rec["usernames_to_read"])
                        except (json.JSONDecodeError, TypeError):
                            rec["usernames_to_read"] = []
                    if rec.get("usernames_to_read") is None:
                        rec["usernames_to_read"] = []
                    rec["instagrapi_session"] = _normalize_session(rec.get("instagrapi_session"))
                    result.append(rec)
                return result
        finally:
            await release_db_connection(conn)

    async def exists_by_source_id(self, user_id: int, domain: str, source_id: str) -> bool:
        """Проверяет, есть ли уже пост с таким instagram_source_id для user_id и domain."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 1 FROM instagram_posts
                    WHERE user_id = %s AND domain = %s AND instagram_source_id = %s
                    LIMIT 1
                    """,
                    (user_id, domain, str(source_id)),
                )
                row = await cur.fetchone()
                return row is not None
        finally:
            await release_db_connection(conn)

    async def save_post(
        self,
        user_id: int,
        instagram_source_id: str,
        domain: str,
        post_text: str,
        post_date: Optional[datetime],
        author: Optional[str],
        images_json: str,
        comments: int,
        likes: int,
    ) -> Optional[int]:
        """Вставляет пост в instagram_posts со статусом collected. Возвращает id или None."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO instagram_posts (
                        user_id, instagram_source_id, domain, post_text, post_date, author,
                        images, comments, likes, status, post_type
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'collected', 'instagram'
                    )
                    RETURNING id
                    """,
                    (
                        user_id,
                        instagram_source_id,
                        domain,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        likes,
                    ),
                )
                row = await cur.fetchone()
                new_id = int(row[0]) if row else None
                _log_action(
                    "Saved instagram post id=%s user_id=%s domain=%s source_id=%s",
                    new_id,
                    user_id,
                    domain,
                    instagram_source_id,
                )
                return new_id
        except Exception as e:
            logger.error("Error saving instagram post: %s", e, exc_info=True)
            return None
        finally:
            await release_db_connection(conn)

    def _taken_at(self, m: Dict[str, Any]) -> Optional[datetime]:
        post_date = m.get("taken_at")
        if isinstance(post_date, datetime):
            return post_date
        if post_date and hasattr(post_date, "timestamp"):
            return datetime.utcfromtimestamp(post_date.timestamp())
        return None

    async def _save_media_items(
        self,
        user_id: int,
        domain: str,
        author: str,
        medias: List[Dict[str, Any]],
    ) -> int:
        saved = 0
        for m in medias:
            pk = m.get("pk") or m.get("id")
            if not pk:
                continue
            source_id = str(pk)
            if await self.exists_by_source_id(user_id, domain, source_id):
                continue
            images_list = m.get("images") or []
            images_json = json.dumps(images_list)
            new_id = await self.save_post(
                user_id=user_id,
                instagram_source_id=source_id,
                domain=domain,
                post_text=(m.get("caption") or "")[:2200],
                post_date=self._taken_at(m),
                author=author,
                images_json=images_json,
                comments=m.get("comment_count") or 0,
                likes=m.get("like_count") or 0,
            )
            if new_id is not None:
                saved += 1
                if images_list and getattr(settings, "COLLECT_MIRROR_IMAGES_TO_S3", True):
                    await mirror_collected_images_to_storage(new_id, user_id, images_list)
        return saved

    async def run_collect(self) -> int:
        """Собирает посты: свои + по каждому username из usernames_to_read. Возвращает число сохранённых."""
        profiles = await self.get_profiles_for_collect()
        if not profiles:
            return 0
        saved = 0
        for profile in profiles:
            user_id = profile["user_id"]
            username = (profile.get("username") or "").strip()
            password = profile.get("password") or ""
            if not username or not password:
                continue
            usernames_to_read = profile.get("usernames_to_read") or []
            if not isinstance(usernames_to_read, list):
                usernames_to_read = []
            client = InstagramClient(
                username,
                password,
                user_id=user_id,
                session_dict=profile.get("instagrapi_session"),
                verification_code=profile.get("instagram_verification_code"),
            )
            if not await client.login():
                logger.warning("Instagram login failed for user_id=%s", user_id)
                continue
            self_uid = await client.get_self_user_id()
            if self_uid:
                medias = await client.user_medias(self_uid, amount=20)
                saved += await self._save_media_items(user_id, username, username, medias)
            for uname in usernames_to_read:
                if not uname or not str(uname).strip():
                    continue
                uname = str(uname).strip()
                uid = await client.user_id_from_username(uname)
                if uid is None:
                    continue
                medias = await client.user_medias(uid, amount=20)
                saved += await self._save_media_items(user_id, uname, uname, medias)
        return saved
