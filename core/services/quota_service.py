"""Квоты по тарифу пользователя (синхронизировать с auth/billing/plan_definitions.py)."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone
from typing import Optional

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


async def count_user_posts_in_current_month(
    user_id: int,
    *,
    now: Optional[datetime] = None,
) -> int:
    """Сумма строк во всех таблицах *_posts за календарный месяц (UTC)."""
    start, end = _month_start_end_utc(now)
    start_naive = start.replace(tzinfo=None)
    end_naive = end.replace(tzinfo=None)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            total = 0
            for table in _POST_TABLES:
                await cur.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE user_id = %s AND created_at >= %s AND created_at <= %s",
                    (user_id, start_naive, end_naive),
                )
                row = await cur.fetchone()
                total += int(row[0] if row else 0)
            return total
    finally:
        await release_db_connection(conn)


async def get_user_tariff(user_id: int) -> str:
    """Читает tariff из общей таблицы users."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT tariff FROM users WHERE id = %s", (user_id,))
            row = await cur.fetchone()
            if not row:
                return "free"
            return str(row[0] or "free")
    finally:
        await release_db_connection(conn)


async def ensure_monthly_post_quota(user_id: int) -> None:
    """Бросает QuotaExceededError, если лимит постов в месяц исчерпан."""
    tariff = await get_user_tariff(user_id)
    limit = _monthly_limit_for_tariff(tariff)
    used = await count_user_posts_in_current_month(user_id)
    if used >= limit:
        raise QuotaExceededError(resource="monthly_posts", limit=limit, used=used)
