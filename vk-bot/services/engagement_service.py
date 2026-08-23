"""Периодическое обновление engagement-метрик опубликованных VK-постов."""

from __future__ import annotations

import logging
from typing import Optional

from database import get_db_connection, release_db_connection
from .vk_client import VkClient
from .channel_counter import record_post_metric_snapshot

logger = logging.getLogger(__name__)


class VkEngagementService:
    async def refresh_engagement(self, limit: int = 50) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT p.id, p.user_id, p.published_vk_post_id, p.published_owner_id,
                           pr.access_token, pr.user_access_token
                    FROM vk_posts p
                    JOIN vk_profiles pr ON pr.user_id = p.user_id
                    WHERE p.status = 'published'
                      AND p.published_vk_post_id IS NOT NULL
                      AND p.published_owner_id IS NOT NULL
                    ORDER BY p.updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        updated = 0
        for post_id, user_id, vk_post_id, owner_id, token, user_token in rows:
            client = self._client_for_owner(int(owner_id), token, user_token)
            if client is None:
                continue
            try:
                items = await client.wall_get_by_id(int(owner_id), int(vk_post_id))
                if not items:
                    continue
                item = items[0]
                views = (item.get("views") or {}).get("count", 0) if isinstance(item.get("views"), dict) else (item.get("views") or 0)
                likes = (item.get("likes") or {}).get("count", 0) or 0
                reposts = (item.get("reposts") or {}).get("count", 0) or 0
                comments = (item.get("comments") or {}).get("count", 0) or 0
                conn = await get_db_connection()
                try:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            UPDATE vk_posts
                            SET views = %s, likes = %s, reposts = %s, comments = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (int(views), int(likes), int(reposts), int(comments), post_id),
                        )
                        await cur.execute(
                            """
                            UPDATE posts
                            SET views = %s, likes = %s, reposts = %s, comments = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE source_platform = 'vk' AND source_id = %s
                            """,
                            (int(views), int(likes), int(reposts), int(comments), post_id),
                        )
                finally:
                    await release_db_connection(conn)
                await record_post_metric_snapshot(
                    user_id,
                    post_id,
                    views=int(views),
                    likes=int(likes),
                    comments=int(comments),
                    reposts=int(reposts),
                )
                updated += 1
            except Exception as exc:
                logger.warning("VK engagement refresh failed for post %s: %s", post_id, exc)
        return updated

    @staticmethod
    def _client_for_owner(
        owner_id: int,
        access_token: Optional[str],
        user_access_token: Optional[str],
    ) -> Optional[VkClient]:
        if owner_id < 0 and access_token:
            return VkClient(access_token)
        if user_access_token:
            return VkClient(user_access_token)
        if access_token:
            return VkClient(access_token)
        return None
