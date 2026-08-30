"""Сервис Telegram-аналитики на основе tg_events и tg_posts."""

from __future__ import annotations

import csv
import io
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


def _chat_clause(chat_id: Optional[str], params: list) -> str:
    if not chat_id:
        return ""
    try:
        params.append(int(str(chat_id).strip()))
        return " AND chat_id = %s"
    except (TypeError, ValueError):
        return ""


class TgAnalyticsService:
    """Агрегация метрик Telegram."""

    async def get_overview(
        self,
        user_id: int,
        period: str = "7d",
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                base_params: list = [user_id, since]
                chat_sql = _chat_clause(chat_id, base_params)

                await cur.execute(
                    f"""
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'collected' AND created_at >= %s
                    {chat_sql}
                    """,
                    tuple(base_params),
                )
                collected = (await cur.fetchone())[0]

                params_sent = [user_id, since]
                chat_sent = _chat_clause(chat_id, params_sent)
                await cur.execute(
                    f"""
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'alert_sent' AND created_at >= %s
                    {chat_sent}
                    """,
                    tuple(params_sent),
                )
                alerts_sent = (await cur.fetchone())[0]

                params_sup = [user_id, since]
                chat_sup = _chat_clause(chat_id, params_sup)
                await cur.execute(
                    f"""
                    SELECT COUNT(*) FROM tg_events
                    WHERE user_id = %s AND event_type = 'alert_suppressed' AND created_at >= %s
                    {chat_sup}
                    """,
                    tuple(params_sup),
                )
                suppressed = (await cur.fetchone())[0]

                params_ch = [user_id, since]
                chat_ch = _chat_clause(chat_id, params_ch)
                await cur.execute(
                    f"""
                    SELECT COUNT(DISTINCT chat_id) FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    {chat_ch}
                    """,
                    tuple(params_ch),
                )
                unique_channels = (await cur.fetchone())[0]

                params_top = [user_id, since]
                chat_top = _chat_clause(chat_id, params_top)
                await cur.execute(
                    f"""
                    SELECT chat_id, COUNT(*) AS cnt FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    {chat_top}
                    GROUP BY chat_id ORDER BY cnt DESC LIMIT 1
                    """,
                    tuple(params_top),
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
                    "chat_id": chat_id,
                }
        finally:
            await release_db_connection(conn)

    async def get_channels(
        self,
        user_id: int,
        period: str = "7d",
        limit: int = 10,
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: list = [user_id, since]
                chat_sql = _chat_clause(chat_id, params)
                params.append(limit)
                await cur.execute(
                    f"""
                    SELECT chat_id, COUNT(*) AS cnt FROM tg_events
                    WHERE user_id = %s AND created_at >= %s AND chat_id IS NOT NULL
                    {chat_sql}
                    GROUP BY chat_id ORDER BY cnt DESC LIMIT %s
                    """,
                    tuple(params),
                )
                rows = await cur.fetchall()
                return [
                    {"chat_id": str(row[0]), "name": str(row[0]), "count": row[1]}
                    for row in rows
                ]
        finally:
            await release_db_connection(conn)

    async def get_keywords(
        self,
        user_id: int,
        period: str = "7d",
        limit: int = 20,
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: list = [user_id, since]
                chat_sql = _chat_clause(chat_id, params)
                await cur.execute(
                    f"""
                    SELECT matched_conditions FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                      AND matched_conditions IS NOT NULL
                      AND event_type = 'alert_sent'
                    {chat_sql}
                    """,
                    tuple(params),
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
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: list = [user_id, since]
                chat_sql = _chat_clause(chat_id, params)
                params.append(limit)
                await cur.execute(
                    f"""
                    SELECT rule_id, event_type, chat_id, matched_conditions, created_at, metadata
                    FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                      AND event_type IN ('alert_sent', 'alert_suppressed', 'alert_matched')
                    {chat_sql}
                    ORDER BY created_at DESC LIMIT %s
                    """,
                    tuple(params),
                )
                rows = await cur.fetchall()
                result = []
                for rule_id, event_type, chat_id_val, matched, created_at, metadata in rows:
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
                            "chat_id": str(chat_id_val) if chat_id_val is not None else None,
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
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - _parse_period(period)
        trunc = "hour" if granularity == "hour" else "day"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: list = [trunc, user_id, since]
                chat_sql = _chat_clause(chat_id, params)
                await cur.execute(
                    f"""
                    SELECT date_trunc(%s, created_at) AS bucket, event_type, COUNT(*)
                    FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                    {chat_sql}
                    GROUP BY bucket, event_type
                    ORDER BY bucket
                    """,
                    tuple(params),
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

    async def get_sentiment_breakdown(
        self,
        user_id: int,
        period: str = "7d",
        chat_id: Optional[str] = None,
    ) -> Dict[str, int]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if chat_id:
                    try:
                        chat_int = int(str(chat_id).strip())
                    except (TypeError, ValueError):
                        chat_int = None
                    if chat_int is not None:
                        await cur.execute(
                            """
                            SELECT metadata FROM tg_posts
                            WHERE user_id = %s AND created_at >= %s AND metadata IS NOT NULL
                              AND (
                                domain = %s OR domain = %s
                                OR telegram_chat_id = %s OR telegram_chat_id = %s
                              )
                            """,
                            (
                                user_id,
                                since,
                                str(chat_int),
                                str(chat_id).strip(),
                                str(chat_int),
                                str(chat_id).strip(),
                            ),
                        )
                    else:
                        await cur.execute(
                            """
                            SELECT metadata FROM tg_posts
                            WHERE user_id = %s AND created_at >= %s AND metadata IS NOT NULL
                            """,
                            (user_id, since),
                        )
                else:
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
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                chat_filter = ""
                params_sum: list = [user_id, since]
                if chat_id:
                    chat_filter = " AND (telegram_chat_id = %s OR domain = %s)"
                    params_sum.extend([str(chat_id).strip(), str(chat_id).strip()])

                await cur.execute(
                    f"""
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
                    {chat_filter}
                    """,
                    tuple(params_sum),
                )
                row = await cur.fetchone()
                total_views, total_likes, total_comments, total_reposts, published_count = row

                params_top: list = [user_id, since]
                if chat_id:
                    params_top.extend([str(chat_id).strip(), str(chat_id).strip()])
                params_top.append(limit)
                await cur.execute(
                    f"""
                    SELECT id, post_text, views, likes, comments, reposts, publish_at, created_at
                    FROM tg_posts
                    WHERE user_id = %s
                      AND status = 'published'
                      AND updated_at >= %s
                    {chat_filter}
                    ORDER BY views DESC NULLS LAST, likes DESC
                    LIMIT %s
                    """,
                    tuple(params_top),
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
            "chat_id": chat_id,
        }

    async def get_health(self, user_id: int, period: str = "24h") -> Dict[str, Any]:
        since = datetime.utcnow() - _parse_period(period)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT event_type, COUNT(*) FROM tg_events
                    WHERE user_id = %s AND created_at >= %s
                      AND event_type IN ('alert_sent', 'alert_suppressed', 'collected')
                    GROUP BY event_type
                    """,
                    (user_id, since),
                )
                counts = {row[0]: int(row[1]) for row in await cur.fetchall()}
                await cur.execute(
                    """
                    SELECT COUNT(*) FROM tg_digests
                    WHERE user_id = %s AND created_at >= %s
                    """,
                    (user_id, since),
                )
                digests = int((await cur.fetchone())[0] or 0)
        finally:
            await release_db_connection(conn)

        return {
            "period": period,
            "alert_sent": counts.get("alert_sent", 0),
            "alert_suppressed": counts.get("alert_suppressed", 0),
            "collected": counts.get("collected", 0),
            "digests": digests,
            "suppression_rate": (
                round(
                    counts.get("alert_suppressed", 0)
                    / max(
                        counts.get("alert_sent", 0) + counts.get("alert_suppressed", 0),
                        1,
                    ),
                    3,
                )
            ),
        }

    async def get_recent_digests(
        self,
        user_id: int,
        limit: int = 5,
        chat_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                params: list = [user_id]
                chat_sql = ""
                if chat_id:
                    chat_sql = _chat_clause(chat_id, params)
                params.append(limit)
                await cur.execute(
                    f"""
                    SELECT id, chat_id, digest_text, message_count, created_at
                    FROM tg_digests
                    WHERE user_id = %s
                    {chat_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                rows = await cur.fetchall()
                return [
                    {
                        "id": row[0],
                        "chat_id": str(row[1]),
                        "digest_text": row[2],
                        "message_count": int(row[3] or 0),
                        "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                    }
                    for row in rows
                ]
        finally:
            await release_db_connection(conn)

    def export_overview_csv(
        self,
        overview: Dict[str, Any],
        channels: List[Dict[str, Any]],
        keywords: List[Dict[str, Any]],
    ) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["section", "key", "value"])
        for key in (
            "messages_collected",
            "alerts_sent",
            "alerts_suppressed",
            "unique_channels",
            "period",
            "chat_id",
        ):
            writer.writerow(["overview", key, overview.get(key, "")])
        for ch in channels:
            writer.writerow(["channel", ch.get("chat_id"), ch.get("count")])
        for kw in keywords:
            writer.writerow(["keyword", kw.get("keyword"), kw.get("count")])
        return buf.getvalue()


tg_analytics_service = TgAnalyticsService()
