"""Сбор engagement-метрик (views / reactions) для опубликованных постов."""

import logging
from typing import Dict, Optional

from database import get_db_connection, release_db_connection
from .client_manager import TelegramClientManager
from .post_publisher import PostPublisher
from .channel_counter import record_post_metric_snapshot

logger = logging.getLogger(__name__)


class EngagementService:
    """Периодически обновляет views/likes у published постов."""

    def __init__(self, client_manager: TelegramClientManager):
        self.client_manager = client_manager
        self._parser = PostPublisher(client_manager)

    async def refresh_engagement(
        self,
        limit: int = 100,
        *,
        hot_days: int = 7,
        hot_cap: int = 300,
        sample_older: int = 50,
    ) -> int:
        """Hot window (7d) + sample of older posts. Returns number of updates."""
        rows = await self._select_posts_for_refresh(
            hot_days=hot_days, hot_cap=hot_cap, sample_older=sample_older, limit=limit
        )
        return await self._refresh_rows(rows)

    async def refresh_one(self, user_id: int, post_id: int) -> dict:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT t.id, t.user_id,
                           NULLIF(t.result->>'telegram_message_id', '')::bigint,
                           t.result->>'telegram_chat_id'
                    FROM post_targets t
                    WHERE t.id = %s AND t.user_id = %s AND t.platform = 'tg'
                      AND t.status = 'published'
                      AND t.result->>'telegram_message_id' IS NOT NULL
                      AND COALESCE(t.result->>'telegram_chat_id', '') != ''
                    """,
                    (post_id, user_id),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)
        if not row:
            return {"ok": False, "error": "post_not_found"}
        updated = await self._refresh_rows([row])
        return {"ok": updated > 0, "updated": updated}

    async def _select_posts_for_refresh(
        self,
        *,
        hot_days: int,
        hot_cap: int,
        sample_older: int,
        limit: int,
    ) -> list:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT t.id, t.user_id,
                           NULLIF(t.result->>'telegram_message_id', '')::bigint,
                           t.result->>'telegram_chat_id'
                    FROM post_targets t
                    WHERE t.platform = 'tg' AND t.status = 'published'
                      AND t.result->>'telegram_message_id' IS NOT NULL
                      AND COALESCE(t.result->>'telegram_chat_id', '') != ''
                      AND COALESCE(t.publish_at, t.created_at) >= NOW() - make_interval(days => %s)
                    ORDER BY COALESCE(t.publish_at, t.created_at) DESC
                    LIMIT %s
                    """,
                    (hot_days, hot_cap),
                )
                hot = list(await cur.fetchall() or [])
                hot_ids = {r[0] for r in hot}
                await cur.execute(
                    """
                    SELECT t.id, t.user_id,
                           NULLIF(t.result->>'telegram_message_id', '')::bigint,
                           t.result->>'telegram_chat_id'
                    FROM post_targets t
                    WHERE t.platform = 'tg' AND t.status = 'published'
                      AND t.result->>'telegram_message_id' IS NOT NULL
                      AND COALESCE(t.result->>'telegram_chat_id', '') != ''
                      AND COALESCE(t.publish_at, t.created_at) < NOW() - make_interval(days => %s)
                    ORDER BY t.updated_at ASC NULLS FIRST
                    LIMIT %s
                    """,
                    (hot_days, sample_older),
                )
                older = [r for r in (await cur.fetchall() or []) if r[0] not in hot_ids]
                combined = hot + older
                return combined[: max(limit, hot_cap + sample_older)]
        finally:
            await release_db_connection(conn)

    async def _refresh_rows(self, rows: list) -> int:
        updated = 0
        metrics_by_post: list[tuple[int, int, int, int, int]] = []
        for post_id, user_id, msg_id, chat_id in rows:
            try:
                metrics = await self._fetch_metrics(user_id, chat_id, int(msg_id))
                if metrics is None:
                    continue
                metrics_by_post.append(
                    (
                        metrics.get("views", 0),
                        metrics.get("likes", 0),
                        metrics.get("reposts", 0),
                        metrics.get("comments", 0),
                        post_id,
                    )
                )
                updated += 1
            except Exception as e:
                logger.warning("Engagement refresh failed for post %s: %s", post_id, e)

        if metrics_by_post:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.executemany(
                        """
                        UPDATE posts
                        SET views = %s,
                            likes = %s,
                            reposts = %s,
                            comments = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = (SELECT post_id FROM post_targets WHERE id = %s)
                        """,
                        metrics_by_post,
                    )
            finally:
                await release_db_connection(conn)
            for views, likes, reposts, comments, post_id in metrics_by_post:
                row_user = next((r[1] for r in rows if r[0] == post_id), None)
                if row_user:
                    await record_post_metric_snapshot(
                        row_user,
                        post_id,
                        views=views,
                        likes=likes,
                        comments=comments,
                        reposts=reposts,
                    )

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
