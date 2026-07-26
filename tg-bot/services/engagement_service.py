"""Сбор engagement-метрик (views / reactions) для опубликованных постов."""

import logging
from typing import Dict, Optional

from database import get_db_connection, release_db_connection
from .client_manager import TelegramClientManager
from .post_publisher import PostPublisher

logger = logging.getLogger(__name__)


class EngagementService:
    """Периодически обновляет views/likes у published постов."""

    def __init__(self, client_manager: TelegramClientManager):
        self.client_manager = client_manager
        self._parser = PostPublisher(client_manager)

    async def refresh_engagement(self, limit: int = 50) -> int:
        """Обновляет метрики для последних published постов. Возвращает число обновлений."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, user_id, telegram_message_id, telegram_chat_id
                    FROM tg_posts
                    WHERE status = 'published'
                      AND telegram_message_id IS NOT NULL
                      AND telegram_chat_id IS NOT NULL
                      AND telegram_chat_id != ''
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        updated = 0
        for post_id, user_id, msg_id, chat_id in rows:
            try:
                metrics = await self._fetch_metrics(user_id, chat_id, int(msg_id))
                if metrics is None:
                    continue
                await self._save_metrics(post_id, metrics)
                updated += 1
            except Exception as e:
                logger.warning("Engagement refresh failed for post %s: %s", post_id, e)
        return updated

    async def _fetch_metrics(
        self, user_id: int, chat_id: str, message_id: int
    ) -> Optional[Dict[str, int]]:
        client = self.client_manager.get_client(user_id)
        if not client:
            return None
        channel = self._parser._parse_channel_to_post(str(chat_id))
        if not channel:
            return None
        messages = await client.get_messages(channel, ids=message_id)
        if not messages:
            return None
        msg = messages if not isinstance(messages, list) else (messages[0] if messages else None)
        if not msg:
            return None

        views = int(getattr(msg, "views", None) or 0)
        likes = 0
        reactions = getattr(msg, "reactions", None)
        if reactions is not None:
            results = getattr(reactions, "results", None) or []
            for item in results:
                likes += int(getattr(item, "count", 0) or 0)
        forwards = int(getattr(msg, "forwards", None) or 0)
        replies = 0
        replies_obj = getattr(msg, "replies", None)
        if replies_obj is not None:
            replies = int(getattr(replies_obj, "replies", 0) or 0)

        return {
            "views": views,
            "likes": likes,
            "reposts": forwards,
            "comments": replies,
        }

    async def _save_metrics(self, post_id: int, metrics: Dict[str, int]) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tg_posts
                    SET views = %s,
                        likes = %s,
                        reposts = %s,
                        comments = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        metrics.get("views", 0),
                        metrics.get("likes", 0),
                        metrics.get("reposts", 0),
                        metrics.get("comments", 0),
                        post_id,
                    ),
                )
        finally:
            await release_db_connection(conn)
