"""Лёгкая аналитика VK поверх vk_events (зеркало tg_analytics health/overview)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from database import get_db_connection, release_db_connection


def _parse_period(period: str) -> timedelta:
    match = re.match(r"^(\d+)([dhm])$", (period or "").strip().lower())
    if not match:
        return timedelta(days=7)
    value, unit = int(match.group(1)), match.group(2)
    if unit == "d":
        return timedelta(days=value)
    if unit == "h":
        return timedelta(hours=value)
    return timedelta(minutes=value)


class VkAnalyticsService:
    async def get_overview(self, user_id: int, period: str = "7d") -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT event_type, COUNT(*)
                    FROM vk_events
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY event_type
                    """,
                    (user_id, since),
                )
                counts = {str(r[0]): int(r[1]) for r in await cur.fetchall()}
                await cur.execute(
                    """
                    SELECT COUNT(DISTINCT owner_id)
                    FROM vk_events
                    WHERE user_id = %s AND created_at >= %s AND owner_id IS NOT NULL
                    """,
                    (user_id, since),
                )
                owners = int((await cur.fetchone())[0] or 0)
        finally:
            await release_db_connection(conn)
        return {
            "period": period,
            "collected": counts.get("collected", 0),
            "published": counts.get("published", 0),
            "publish_failed": counts.get("publish_failed", 0),
            "owners": owners,
            "by_type": counts,
        }

    async def get_health(self, user_id: int, period: str = "24h") -> Dict[str, Any]:
        overview = await self.get_overview(user_id, period)
        failed = int(overview.get("publish_failed") or 0)
        published = int(overview.get("published") or 0)
        return {
            "period": period,
            "ok": failed == 0 or published > failed,
            "collected": overview["collected"],
            "published": published,
            "publish_failed": failed,
            "message": (
                "VK publish queue has failures"
                if failed > published
                else "VK event journal healthy"
            ),
        }


vk_analytics_service = VkAnalyticsService()
