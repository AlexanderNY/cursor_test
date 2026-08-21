"""Сервис для сбора статистики постов."""

from typing import List, Dict, Optional

from database import get_db_connection, release_db_connection


class StatisticsService:
    """Сервис для получения статистики по постам."""

    _PLATFORM_FIELDS = (
        ("to_tg", "Telegram"),
        ("to_tw", "Twitter"),
        ("to_wp", "WordPress"),
        ("to_vk", "VKontakte"),
    )

    async def get_statistics(self) -> List[Dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                platform_cases = ", ".join(
                    f"COUNT(*) FILTER (WHERE {field} = TRUE AND status = 'collected') AS {field}_collected,"
                    f" COUNT(*) FILTER (WHERE {field} = TRUE AND status = 'processed') AS {field}_processed,"
                    f" COUNT(*) FILTER (WHERE {field} = TRUE AND status = 'published') AS {field}_published"
                    for field, _ in self._PLATFORM_FIELDS
                )
                await cur.execute(
                    f"""
                    SELECT
                        {platform_cases},
                        COUNT(*) FILTER (WHERE status = 'collected') AS total_collected,
                        COUNT(*) FILTER (WHERE status = 'processed') AS total_processed,
                        COUNT(*) FILTER (WHERE status = 'published') AS total_published
                    FROM posts
                    """
                )
                row = await cur.fetchone()
                if not row:
                    return []

                stats: List[Dict] = []
                offset = 0
                for field, name in self._PLATFORM_FIELDS:
                    stats.append(
                        {
                            "service_name": name,
                            "collected_posts": row[offset],
                            "processed_posts": row[offset + 1],
                            "published_posts": row[offset + 2],
                        }
                    )
                    offset += 3
                stats.append(
                    {
                        "service_name": "Total",
                        "collected_posts": row[offset],
                        "processed_posts": row[offset + 1],
                        "published_posts": row[offset + 2],
                    }
                )
                return stats
        finally:
            await release_db_connection(conn)

    async def get_users_statistics(self, user_ids: Optional[List[int]] = None) -> List[Dict]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if user_ids is not None and len(user_ids) == 0:
                    return []
                if user_ids is not None:
                    placeholders = ",".join(["%s"] * len(user_ids))
                    await cur.execute(
                        f"""
                        SELECT
                            user_id,
                            COUNT(*) AS total_posts,
                            COUNT(*) FILTER (WHERE status = 'collected') AS collected_posts,
                            COUNT(*) FILTER (WHERE status = 'processed') AS processed_posts,
                            COUNT(*) FILTER (WHERE status = 'published') AS published_posts
                        FROM posts
                        WHERE user_id IN ({placeholders})
                        GROUP BY user_id
                        ORDER BY total_posts DESC
                        """,
                        tuple(user_ids),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT
                            user_id,
                            COUNT(*) AS total_posts,
                            COUNT(*) FILTER (WHERE status = 'collected') AS collected_posts,
                            COUNT(*) FILTER (WHERE status = 'processed') AS processed_posts,
                            COUNT(*) FILTER (WHERE status = 'published') AS published_posts
                        FROM posts
                        GROUP BY user_id
                        ORDER BY total_posts DESC
                        """
                    )
                rows = await cur.fetchall()
                return [
                    {
                        "user_id": row[0],
                        "total_posts": row[1],
                        "collected_posts": row[2],
                        "processed_posts": row[3],
                        "published_posts": row[4],
                    }
                    for row in rows
                ]
        finally:
            await release_db_connection(conn)


statistics_service = StatisticsService()
