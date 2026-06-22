"""Публикация tw_posts со статусом ready в X через API v2."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

from .x_client import create_tweet, ensure_user_access_token

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    from config import settings

    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class PostPublisher:
    """Публикация в X для строк tw_posts (status=ready, to_tw=true)."""

    async def _get_ready_posts(self) -> List[Dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.user_id, p.post_text, p.images,
                           pr.twitter_oauth_access_token, pr.twitter_oauth_refresh_token,
                           pr.twitter_oauth_expires_at
                    FROM tw_posts p
                    INNER JOIN tw_profiles pr ON p.user_id = pr.user_id
                    WHERE p.status = 'ready'
                      AND p.to_tw = TRUE
                      AND pr.twitter_oauth_refresh_token IS NOT NULL
                      AND pr.twitter_oauth_refresh_token != ''
                    ORDER BY p.created_at ASC
                    LIMIT 20
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        finally:
            await release_db_connection(conn)

    async def _persist_tokens(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: Optional[datetime],
    ) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tw_profiles SET
                        twitter_oauth_access_token = %s,
                        twitter_oauth_refresh_token = COALESCE(%s, twitter_oauth_refresh_token),
                        twitter_oauth_expires_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (access_token, refresh_token, expires_at, user_id),
                )
        finally:
            await release_db_connection(conn)

    async def _update_post_published(self, post_id: int, tweet_id: str) -> None:
        permalink = f"https://x.com/i/web/status/{tweet_id}"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tw_posts SET status = 'published', url = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (permalink, post_id),
                )
        finally:
            await release_db_connection(conn)

    async def _mark_failed(self, post_id: int, hint: str) -> None:
        logger.error("tw_posts id=%s publish failed: %s", post_id, hint)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE tw_posts SET status = 'failed', image_over_text = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (hint[:500], post_id),
                )
        finally:
            await release_db_connection(conn)

    async def publish_one(self, post: Dict[str, Any]) -> bool:
        post_id = post["id"]
        user_id = post["user_id"]
        text = (post.get("post_text") or "").strip()
        if not text:
            await self._mark_failed(post_id, "empty post_text")
            return False

        acc = post.get("twitter_oauth_access_token")
        ref = post.get("twitter_oauth_refresh_token")
        exp = post.get("twitter_oauth_expires_at")

        new_acc, new_ref, new_exp = await ensure_user_access_token(acc, ref, exp)
        if not new_acc:
            await self._mark_failed(post_id, "no valid OAuth access token")
            return False

        if new_acc != acc or (new_ref and new_ref != ref) or new_exp != exp:
            await self._persist_tokens(user_id, new_acc, new_ref, new_exp)

        result = await create_tweet(new_acc, text)
        if not result or not (result.get("data") or {}).get("id"):
            await self._mark_failed(post_id, json.dumps(result or {})[:500])
            return False

        tid = str(result["data"]["id"])
        await self._update_post_published(post_id, tid)
        _log_action("Published tw_posts id=%s -> tweet %s", post_id, tid)
        return True

    async def publish_ready_posts(self) -> int:
        posts = await self._get_ready_posts()
        n = 0
        for p in posts:
            try:
                if await self.publish_one(p):
                    n += 1
            except Exception as e:
                logger.exception("publish_one id=%s: %s", p.get("id"), e)
        return n
