"""Квоты по тарифу пользователя (синхронизировать с auth/billing/plan_definitions.py)."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone
from typing import Any, Optional

from database import get_db_connection, release_db_connection

from exceptions import QuotaExceededError

# Должно совпадать с auth/billing/plan_definitions.py (monthly_posts_limit)
_TARIFF_MONTHLY_POSTS: dict[str, int] = {
    "free": 300,
    "basic": 3000,
    "premium": 50000,
}

_POST_TABLES = (
    "posts",
    "wp_posts",
    "tg_posts",
    "tw_posts",
    "vk_posts",
    "cpost_posts",
    "threads_posts",
    "dzen_posts",
    "instagram_posts",
    "url_posts",
)


def _monthly_limit_for_tariff(tariff: Optional[str]) -> int:
    t = (tariff or "free").strip().lower()
    return _TARIFF_MONTHLY_POSTS.get(t, _TARIFF_MONTHLY_POSTS["free"])


def _month_start_end_utc(now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    n = now or datetime.now(timezone.utc)
    start = datetime(n.year, n.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    last = monthrange(n.year, n.month)[1]
    end = datetime(n.year, n.month, last, 23, 59, 59, 999999, tzinfo=timezone.utc)
    return start, end


def _count_posts_sql() -> str:
    parts = [
        f"SELECT COUNT(*)::bigint AS c FROM {table} "
        f"WHERE user_id = %s AND created_at >= %s AND created_at <= %s"
        for table in _POST_TABLES
    ]
    return f"SELECT COALESCE(SUM(c), 0) FROM ({' UNION ALL '.join(parts)}) t"


async def count_user_posts_in_current_month(
    user_id: int,
    *,
    now: Optional[datetime] = None,
    conn: Any = None,
) -> int:
    """Сумма строк во всех таблицах *_posts за календарный месяц (UTC). Один SQL."""
    start, end = _month_start_end_utc(now)
    start_naive = start.replace(tzinfo=None)
    end_naive = end.replace(tzinfo=None)
    params: list[Any] = []
    for _ in _POST_TABLES:
        params.extend([user_id, start_naive, end_naive])

    own_conn = conn is None
    if own_conn:
        conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(_count_posts_sql(), params)
            row = await cur.fetchone()
            return int(row[0] if row else 0)
    finally:
        if own_conn:
            await release_db_connection(conn)


async def get_user_tariff(user_id: int, *, conn: Any = None) -> str:
    """Читает tariff из общей таблицы users."""
    own_conn = conn is None
    if own_conn:
        conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT tariff FROM users WHERE id = %s", (user_id,))
            row = await cur.fetchone()
            if not row:
                return "free"
            return str(row[0] or "free")
    finally:
        if own_conn:
            await release_db_connection(conn)


async def ensure_monthly_post_quota(user_id: int, *, conn: Any = None) -> None:
    """Бросает QuotaExceededError, если лимит постов в месяц исчерпан.

    При переданном conn — tariff и COUNT на одном соединении (без лишних acquire).
    """
    own_conn = conn is None
    if own_conn:
        conn = await get_db_connection()
    try:
        tariff = await get_user_tariff(user_id, conn=conn)
        limit = _monthly_limit_for_tariff(tariff)
        used = await count_user_posts_in_current_month(user_id, conn=conn)
        if used >= limit:
            raise QuotaExceededError(resource="monthly_posts", limit=limit, used=used)
    finally:
        if own_conn:
            await release_db_connection(conn)
