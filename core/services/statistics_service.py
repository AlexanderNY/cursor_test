"""Сервис для сбора статистики постов."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection
from services.pipeline_effectiveness import success_rate

_HUB_COLLECTED = ("collected", "created")
_HUB_PROCESSED = ("processing", "ready", "review", "digest_hold", "digested")
_COLLECTED_SQL = ", ".join(f"'{s}'" for s in _HUB_COLLECTED)
_PROCESSED_SQL = ", ".join(f"'{s}'" for s in _HUB_PROCESSED)
_ALLOWED_PERIOD_DAYS = (7, 30, 90)


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
                    f"COUNT(*) FILTER (WHERE {field} = TRUE AND status IN ({_COLLECTED_SQL})) AS {field}_collected,"
                    f" COUNT(*) FILTER (WHERE {field} = TRUE AND status IN ({_PROCESSED_SQL})) AS {field}_processed,"
                    f" COUNT(*) FILTER (WHERE {field} = TRUE AND EXISTS ("
                    f"SELECT 1 FROM post_targets t WHERE t.post_id = posts.id "
                    f"AND t.platform = '{self._flag_platform(field)}' AND t.status = 'published'"
                    f")) AS {field}_published"
                    for field, _ in self._PLATFORM_FIELDS
                )
                await cur.execute(
                    f"""
                    SELECT
                        {platform_cases},
                        COUNT(*) FILTER (WHERE status IN ({_COLLECTED_SQL})) AS total_collected,
                        COUNT(*) FILTER (WHERE status IN ({_PROCESSED_SQL})) AS total_processed,
                        COUNT(*) FILTER (WHERE EXISTS (
                            SELECT 1 FROM post_targets t
                            WHERE t.post_id = posts.id AND t.status = 'published'
                        )) AS total_published
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
                            COUNT(*) FILTER (WHERE status IN ({_COLLECTED_SQL})) AS collected_posts,
                            COUNT(*) FILTER (WHERE status IN ({_PROCESSED_SQL})) AS processed_posts,
                            COUNT(*) FILTER (WHERE EXISTS (
                                SELECT 1 FROM post_targets t
                                WHERE t.post_id = posts.id AND t.status = 'published'
                            )) AS published_posts
                        FROM posts
                        WHERE user_id IN ({placeholders})
                        GROUP BY user_id
                        ORDER BY total_posts DESC
                        """,
                        tuple(user_ids),
                    )
                else:
                    await cur.execute(
                        f"""
                        SELECT
                            user_id,
                            COUNT(*) AS total_posts,
                            COUNT(*) FILTER (WHERE status IN ({_COLLECTED_SQL})) AS collected_posts,
                            COUNT(*) FILTER (WHERE status IN ({_PROCESSED_SQL})) AS processed_posts,
                            COUNT(*) FILTER (WHERE EXISTS (
                                SELECT 1 FROM post_targets t
                                WHERE t.post_id = posts.id AND t.status = 'published'
                            )) AS published_posts
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

    @staticmethod
    def _flag_platform(field: str) -> str:
        return {
            "to_tg": "tg",
            "to_tw": "tw",
            "to_wp": "wp",
            "to_vk": "vk",
        }.get(field, field)

    async def get_pipeline_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Агрегат эффективности за период: успех, ошибки, латентность, застрявшие очереди."""
        period_days = int(days) if int(days) in _ALLOWED_PERIOD_DAYS else 30
        since = datetime.now(timezone.utc) - timedelta(days=period_days)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        platform,
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = 'published') AS published,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed,
                        COUNT(*) FILTER (WHERE status = 'skipped') AS skipped,
                        COUNT(*) FILTER (WHERE status IN ('pending', 'ready', 'publishing')) AS in_queue
                    FROM post_targets
                    WHERE updated_at >= %s
                    GROUP BY platform
                    ORDER BY platform
                    """,
                    (since,),
                )
                platform_rows = await cur.fetchall()

                await cur.execute(
                    """
                    SELECT
                        COALESCE(NULLIF(LEFT(COALESCE(result->>'error', ''), 160), ''), 'unknown') AS reason,
                        COUNT(*) AS cnt
                    FROM post_targets
                    WHERE status = 'failed'
                      AND updated_at >= %s
                    GROUP BY 1
                    ORDER BY cnt DESC, reason
                    LIMIT 20
                    """,
                    (since,),
                )
                failure_rows = await cur.fetchall()

                await cur.execute("SELECT to_regclass('public.post_lifecycle_events')")
                has_lifecycle = (await cur.fetchone() or (None,))[0] is not None
                if has_lifecycle:
                    latency_sql = """
                    SELECT
                        COUNT(*)::int,
                        percentile_cont(0.5) WITHIN GROUP (ORDER BY mins),
                        percentile_cont(0.95) WITHIN GROUP (ORDER BY mins)
                    FROM (
                        SELECT EXTRACT(EPOCH FROM (
                            COALESCE(life_end.published_at, published.published_at)
                            - COALESCE(life_start.collected_at, published.hub_created)
                        )) / 60.0 AS mins
                        FROM (
                            SELECT
                                t.post_id,
                                t.platform,
                                t.updated_at AS published_at,
                                p.created_at AS hub_created
                            FROM post_targets t
                            JOIN posts p ON p.id = t.post_id
                            WHERE t.status = 'published'
                              AND t.updated_at >= %s
                              AND p.created_at IS NOT NULL
                        ) published
                        LEFT JOIN (
                            SELECT post_id, MIN(created_at) AS collected_at
                            FROM post_lifecycle_events
                            WHERE to_status IN ('collected', 'created')
                            GROUP BY post_id
                        ) life_start ON life_start.post_id = published.post_id
                        LEFT JOIN (
                            SELECT post_id, platform, MIN(created_at) AS published_at
                            FROM post_lifecycle_events
                            WHERE to_status = 'published'
                            GROUP BY post_id, platform
                        ) life_end
                          ON life_end.post_id = published.post_id
                         AND life_end.platform = published.platform
                        WHERE COALESCE(life_end.published_at, published.published_at)
                              >= COALESCE(life_start.collected_at, published.hub_created)
                    ) samples
                    """
                else:
                    latency_sql = """
                    SELECT
                        COUNT(*)::int,
                        percentile_cont(0.5) WITHIN GROUP (ORDER BY mins),
                        percentile_cont(0.95) WITHIN GROUP (ORDER BY mins)
                    FROM (
                        SELECT EXTRACT(EPOCH FROM (t.updated_at - p.created_at)) / 60.0 AS mins
                        FROM post_targets t
                        JOIN posts p ON p.id = t.post_id
                        WHERE t.status = 'published'
                          AND t.updated_at >= %s
                          AND p.created_at IS NOT NULL
                          AND t.updated_at >= p.created_at
                    ) samples
                    """
                await cur.execute(latency_sql, (since,))
                latency_row = await cur.fetchone() or (0, None, None)

                await cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status IN ('collected', 'created')),
                        COUNT(*) FILTER (WHERE status = 'processing'),
                        COUNT(*) FILTER (WHERE status = 'review'),
                        COUNT(*) FILTER (WHERE status = 'ready'),
                        COUNT(*) FILTER (
                            WHERE status IN ('collected', 'created')
                              AND created_at < NOW() - INTERVAL '1 hour'
                        )
                    FROM posts
                    """
                )
                hub_stuck = await cur.fetchone() or (0, 0, 0, 0, 0)

                await cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status = 'pending'),
                        COUNT(*) FILTER (WHERE status = 'ready'),
                        COUNT(*) FILTER (WHERE status = 'publishing'),
                        COUNT(*) FILTER (
                            WHERE status = 'ready'
                              AND updated_at < NOW() - INTERVAL '1 hour'
                        ),
                        COUNT(*) FILTER (
                            WHERE status = 'publishing'
                              AND updated_at < NOW() - INTERVAL '15 minutes'
                        )
                    FROM post_targets
                    """
                )
                target_stuck = await cur.fetchone() or (0, 0, 0, 0, 0)

                await cur.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM posts WHERE created_at >= %s",
                    (since,),
                )
                users_with_posts = int((await cur.fetchone() or (0,))[0] or 0)
                await cur.execute(
                    """
                    SELECT COUNT(DISTINCT user_id)
                    FROM post_targets
                    WHERE status = 'published' AND updated_at >= %s
                    """,
                    (since,),
                )
                users_with_published = int((await cur.fetchone() or (0,))[0] or 0)
        finally:
            await release_db_connection(conn)

        by_platform: List[Dict[str, Any]] = []
        published = failed = skipped = in_queue = total = 0
        for row in platform_rows:
            item_published = int(row[2] or 0)
            item_failed = int(row[3] or 0)
            item = {
                "platform": row[0],
                "total": int(row[1] or 0),
                "published": item_published,
                "failed": item_failed,
                "skipped": int(row[4] or 0),
                "in_queue": int(row[5] or 0),
                "success_rate": success_rate(item_published, item_failed),
            }
            by_platform.append(item)
            total += item["total"]
            published += item_published
            failed += item_failed
            skipped += item["skipped"]
            in_queue += item["in_queue"]

        sample_size = int(latency_row[0] or 0)
        median = float(latency_row[1]) if latency_row[1] is not None else None
        p95 = float(latency_row[2]) if latency_row[2] is not None else None

        return {
            "period_days": period_days,
            "since": since.isoformat(),
            "targets_total": total,
            "published": published,
            "failed": failed,
            "skipped": skipped,
            "in_queue": in_queue,
            "success_rate": success_rate(published, failed),
            "by_platform": by_platform,
            "failures": [
                {"reason": str(row[0] or "unknown"), "count": int(row[1] or 0)}
                for row in failure_rows
            ],
            "latency": {
                "sample_size": sample_size,
                "median_minutes": round(median, 2) if median is not None else None,
                "p95_minutes": round(p95, 2) if p95 is not None else None,
            },
            "stuck": {
                "posts_collected": int(hub_stuck[0] or 0),
                "posts_processing": int(hub_stuck[1] or 0),
                "posts_review": int(hub_stuck[2] or 0),
                "posts_ready": int(hub_stuck[3] or 0),
                "collected_older_than_1h": int(hub_stuck[4] or 0),
                "targets_pending": int(target_stuck[0] or 0),
                "targets_ready": int(target_stuck[1] or 0),
                "targets_publishing": int(target_stuck[2] or 0),
                "ready_older_than_1h": int(target_stuck[3] or 0),
                "publishing_older_than_15m": int(target_stuck[4] or 0),
            },
            "users_with_posts": users_with_posts,
            "users_with_published": users_with_published,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }


statistics_service = StatisticsService()
