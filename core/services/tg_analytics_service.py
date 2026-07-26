"""Сервис Telegram-аналитики на основе tg_events и tg_posts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection


def _parse_period(period: str) -> timedelta:
    match = re.match(r"^(\d+)([dhm])$", period.strip().lower())
    if not match:
        return timedelta(days=7)
    value, unit = int(match.group(1)), match.group(2)
    if unit == "d":
        return timedelta(days=value)
    if unit == "h":
        return timedelta(hours=value)
    return timedelta(minutes=value)


class TgAnalyticsService:
    """Агрегация метрик Telegram."""

    async def get_overview(self, user_id: int, period: str = "7d") -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'collected' AND created_at >= %s
                    """,
                    (user_id, since),
                )
                collected = (await cur.fetchone())[0]

                await cur.execute(
                    """
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'alert_sent' AND created_at >= %s
                    """,
                    (user_id, since),
                )
                alerts_sent = (await cur.fetchone())[0]

                await cur.execute(
                    """
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'alert_suppressed' AND created_at >= %s
                    """,
                    (user_id, since),
                )
                suppressed = (await cur.fetchone())[0]

                await cur.execute(
                    """
                    SELECT COUNT(DISTINCT chat_id) FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    """,
                    (user_id, since),
                )
                unique_channels = (await cur.fetchone())[0]

                await cur.execute(
                    """
                    SELECT chat_id, COUNT(*) AS cnt FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    GROUP BY chat_id ORDER BY cnt DESC LIMIT 1
                    """,
                    (user_id, since),
                )
                top_row = await cur.fetchone()
                top_channel = None
                if top_row:
                    top_channel = {"chat_id": str(top_row[0]), "name": str(top_row[0]), "count": top_row[1]}

                return {
                    "messages_collected": collected,
                    "alerts_sent": alerts_sent,
                    "alerts_suppressed": suppressed,
                    "unique_channels": unique_channels,
                    "top_channel": top_channel,
                    "period": period,
                }
        finally:
            await release_db_connection(conn)

    async def get_channels(self, user_id: int, period: str = "7d", limit: int = 10) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT chat_id, COUNT(*) AS cnt FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    GROUP BY chat_id ORDER BY cnt DESC LIMIT %s
                    """,
                    (user_id, since, limit),
                )
                rows = await cur.fetchall()
                return [
                    {"chat_id": str(row[0]), "name": str(row[0]), "count": row[1]}
                    for row in rows
                ]
        finally:
            await release_db_connection(conn)

    async def get_keywords(self, user_id: int, period: str = "7d", limit: int = 20) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT matched_conditions FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                      AND matched_conditions IS NOT NULL
                      AND event_type IN ('alert_matched', 'alert_sent')
                    """,
                    (user_id, since),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        counts: Dict[str, int] = {}
        for (raw,) in rows:
            conditions = raw
            if isinstance(raw, str):
                try:
                    conditions = json.loads(raw)
                except json.JSONDecodeError:
                    conditions = []
            if not isinstance(conditions, list):
                continue
            for item in conditions:
                key = str(item).strip()
                if key:
                    counts[key] = counts.get(key, 0) + 1

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"keyword": k, "count": v} for k, v in sorted_items]

    async def get_alerts(
        self,
        user_id: int,
        period: str = "7d",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT rule_id, event_type, chat_id, matched_conditions, created_at, metadata
                    FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                      AND event_type IN ('alert_sent', 'alert_suppressed', 'alert_matched')
                    ORDER BY created_at DESC LIMIT %s
                    """,
                    (user_id, since, limit),
                )
                rows = await cur.fetchall()
                result = []
                for rule_id, event_type, chat_id, matched, created_at, metadata in rows:
                    conditions = matched
                    if isinstance(matched, str):
                        try:
                            conditions = json.loads(matched)
                        except json.JSONDecodeError:
                            conditions = []
                    meta = metadata
                    if isinstance(metadata, str):
                        try:
                            meta = json.loads(metadata)
                        except json.JSONDecodeError:
                            meta = {}
                    result.append(
                        {
                            "rule_id": rule_id,
                            "alert_text": (meta or {}).get("alert_text"),
                            "chat_id": str(chat_id) if chat_id is not None else None,
                            "event_type": event_type,
                            "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                            "matched_conditions": conditions if isinstance(conditions, list) else [],
                        }
                    )
                return result
        finally:
            await release_db_connection(conn)

    async def get_timeline(
        self,
        user_id: int,
        period: str = "7d",
        granularity: str = "hour",
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        trunc = "hour" if granularity == "hour" else "day"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT date_trunc(%s, created_at) AS bucket, event_type, COUNT(*)
                    FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                    GROUP BY bucket, event_type
                    ORDER BY bucket
                    """,
                    (trunc, user_id, since),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        buckets: Dict[str, Dict[str, int]] = {}
        for bucket, event_type, count in rows:
            key = bucket.isoformat() if hasattr(bucket, "isoformat") else str(bucket)
            if key not in buckets:
                buckets[key] = {"collected": 0, "alerts_sent": 0, "alerts_suppressed": 0}
            if event_type == "collected":
                buckets[key]["collected"] += count
            elif event_type == "alert_sent":
                buckets[key]["alerts_sent"] += count
            elif event_type == "alert_suppressed":
                buckets[key]["alerts_suppressed"] += count

        return [
            {"bucket": k, **v}
            for k, v in sorted(buckets.items())
        ]

    async def get_sentiment_breakdown(self, user_id: int, period: str = "7d") -> Dict[str, int]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT metadata FROM tg_posts
                    WHERE user_id = %s AND created_at >= %s AND metadata IS NOT NULL
                    """,
                    (user_id, since),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        breakdown = {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
        for (raw,) in rows:
            meta = raw
            if isinstance(raw, str):
                try:
                    meta = json.loads(raw)
                except json.JSONDecodeError:
                    continue
            if not isinstance(meta, dict):
                continue
            sentiment = str(meta.get("sentiment", "neutral"))
            if sentiment not in breakdown:
                sentiment = "neutral"
            breakdown[sentiment] += 1
            breakdown["total"] += 1
        return breakdown

    async def get_engagement(
        self,
        user_id: int,
        period: str = "7d",
        limit: int = 10,
    ) -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(views), 0),
                        COALESCE(SUM(likes), 0),
                        COALESCE(SUM(comments), 0),
                        COALESCE(SUM(reposts), 0),
                        COUNT(*)
                    FROM tg_posts
                    WHERE user_id = %s
                      AND status = 'published'
                      AND updated_at >= %s
                    """,
                    (user_id, since),
                )
                row = await cur.fetchone()
                total_views, total_likes, total_comments, total_reposts, published_count = row

                await cur.execute(
                    """
                    SELECT id, post_text, views, likes, comments, reposts, publish_at, created_at
                    FROM tg_posts
                    WHERE user_id = %s
                      AND status = 'published'
                      AND updated_at >= %s
                    ORDER BY views DESC NULLS LAST, likes DESC
                    LIMIT %s
                    """,
                    (user_id, since, limit),
                )
                top_rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        published_count = int(published_count or 0)
        total_views = int(total_views or 0)
        total_likes = int(total_likes or 0)
        total_comments = int(total_comments or 0)
        total_reposts = int(total_reposts or 0)
        engagement = total_likes + total_comments + total_reposts
        avg_er = round((engagement / total_views) * 100, 2) if total_views > 0 else 0.0

        top_posts = []
        for r in top_rows:
            pid, text, views, likes, comments, reposts, publish_at, created_at = r
            top_posts.append(
                {
                    "id": pid,
                    "post_text": (text or "")[:200],
                    "views": int(views or 0),
                    "likes": int(likes or 0),
                    "comments": int(comments or 0),
                    "reposts": int(reposts or 0),
                    "publish_at": publish_at.isoformat() if hasattr(publish_at, "isoformat") else publish_at,
                    "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                }
            )

        return {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_reposts": total_reposts,
            "published_count": published_count,
            "avg_er": avg_er,
            "top_posts": top_posts,
            "period": period,
        }


tg_analytics_service = TgAnalyticsService()
