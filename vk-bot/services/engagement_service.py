"""Периодическое обновление engagement-метрик опубликованных VK-постов."""

from __future__ import annotations

import logging
from typing import Optional

from database import get_db_connection, release_db_connection
from .vk_client import VkClient
from .channel_counter import record_post_metric_snapshot

logger = logging.getLogger(__name__)


class VkEngagementService:
    async def refresh_engagement(
        self,
        limit: int = 100,
        *,
        hot_days: int = 7,
        hot_cap: int = 300,
        sample_older: int = 50,
    ) -> int:
        rows = await self._select_posts(hot_days=hot_days, hot_cap=hot_cap, sample_older=sample_older)
        rows = rows[: max(limit, hot_cap + sample_older)]
        return await self._refresh_rows(rows)

    async def refresh_one(self, user_id: int, post_id: int) -> dict:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT t.id, t.user_id,
                           NULLIF(t.result->>'published_vk_post_id', '')::int,
                           NULLIF(t.result->>'published_owner_id', '')::bigint,
                           pr.access_token, pr.user_access_token
                    FROM post_targets t
                    JOIN vk_profiles pr ON pr.user_id = t.user_id
                    WHERE t.id = %s AND t.user_id = %s AND t.platform = 'vk'
                      AND t.status = 'published'
                      AND t.result->>'published_vk_post_id' IS NOT NULL
                      AND t.result->>'published_owner_id' IS NOT NULL
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

    async def _select_posts(
        self, *, hot_days: int, hot_cap: int, sample_older: int
    ) -> list:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT t.id, t.user_id,
                           NULLIF(t.result->>'published_vk_post_id', '')::int,
                           NULLIF(t.result->>'published_owner_id', '')::bigint,
                           pr.access_token, pr.user_access_token
                    FROM post_targets t
                    JOIN vk_profiles pr ON pr.user_id = t.user_id
                    WHERE t.platform = 'vk' AND t.status = 'published'
                      AND t.result->>'published_vk_post_id' IS NOT NULL
                      AND t.result->>'published_owner_id' IS NOT NULL
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
                           NULLIF(t.result->>'published_vk_post_id', '')::int,
                           NULLIF(t.result->>'published_owner_id', '')::bigint,
                           pr.access_token, pr.user_access_token
                    FROM post_targets t
                    JOIN vk_profiles pr ON pr.user_id = t.user_id
                    WHERE t.platform = 'vk' AND t.status = 'published'
                      AND t.result->>'published_vk_post_id' IS NOT NULL
                      AND t.result->>'published_owner_id' IS NOT NULL
                      AND COALESCE(t.publish_at, t.created_at) < NOW() - make_interval(days => %s)
                    ORDER BY t.updated_at ASC NULLS FIRST
                    LIMIT %s
                    """,
                    (hot_days, sample_older),
                )
                older = [r for r in (await cur.fetchall() or []) if r[0] not in hot_ids]
                return hot + older
        finally:
            await release_db_connection(conn)

    async def _refresh_rows(self, rows: list) -> int:
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
                views = (
                    (item.get("views") or {}).get("count", 0)
                    if isinstance(item.get("views"), dict)
                    else (item.get("views") or 0)
                )
                likes = (item.get("likes") or {}).get("count", 0) or 0
                reposts = (item.get("reposts") or {}).get("count", 0) or 0
                comments = (item.get("comments") or {}).get("count", 0) or 0
                conn = await get_db_connection()
                try:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            UPDATE posts
                            SET views = %s, likes = %s, reposts = %s, comments = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = (SELECT post_id FROM post_targets WHERE id = %s)
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
