"""Квоты по тарифу пользователя (синхронизировать с auth/billing/plan_definitions.py)."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone
from typing import Any, Optional

from database import get_db_connection, release_db_connection
from shared.db.post_columns import QUOTA_POST_TABLES

from exceptions import QuotaExceededError

# Зеркало auth/billing/plan_definitions.py
_PLAN_LIMITS: dict[str, dict[str, Any]] = {
    "free": {
        "monthly_posts": 300,
        "max_own_channels": 3,
        "max_brands": 1,
        "max_targets_per_job": 1,
        "max_automations": 0,
        "ai_calls_month": 0,
        "schedule_horizon_days": 7,
        "stats_retention_days": 7,
        "csv_import_rows": 20,
        "features": {
            "inbox_reply": False,
            "inbox_redirect": False,
            "ai_composer": False,
            "automations": False,
            "competitors": False,
            "approval_workflow": False,
            "best_times": False,
            "channel_stats": True,
            "multi_channel_send": True,
            "schedule": True,
        },
    },
    "standard": {
        "monthly_posts": 3000,
        "max_own_channels": 10,
        "max_brands": 5,
        "max_targets_per_job": 5,
        "max_automations": 5,
        "ai_calls_month": 100,
        "schedule_horizon_days": 30,
        "stats_retention_days": 90,
        "csv_import_rows": 200,
        "features": {
            "inbox_reply": True,
            "inbox_redirect": True,
            "ai_composer": True,
            "automations": True,
            "competitors": False,
            "approval_workflow": True,
            "best_times": True,
            "channel_stats": True,
            "multi_channel_send": True,
            "schedule": True,
        },
    },
    "full": {
        "monthly_posts": 50000,
        "max_own_channels": 20,
        "max_brands": 20,
        "max_targets_per_job": 20,
        "max_automations": 50,
        "ai_calls_month": 2000,
        "schedule_horizon_days": 90,
        "stats_retention_days": 365,
        "csv_import_rows": 2000,
        "features": {
            "inbox_reply": True,
            "inbox_redirect": True,
            "ai_composer": True,
            "automations": True,
            "competitors": True,
            "approval_workflow": True,
            "best_times": True,
            "channel_stats": True,
            "multi_channel_send": True,
            "schedule": True,
        },
    },
}

_TARIFF_ALIASES = {"basic": "standard", "premium": "full"}

_POST_TABLES = QUOTA_POST_TABLES


def normalize_tariff(tariff: Optional[str]) -> str:
    t = (tariff or "free").strip().lower()
    return _TARIFF_ALIASES.get(t, t)


def get_plan_limits(tariff: Optional[str]) -> dict[str, Any]:
    t = normalize_tariff(tariff)
    return _PLAN_LIMITS.get(t, _PLAN_LIMITS["free"])


def plan_limit(tariff: Optional[str], key: str, default: int = 0) -> int:
    return int(get_plan_limits(tariff).get(key, default))


def plan_feature(tariff: Optional[str], key: str, default: bool = False) -> bool:
    features = get_plan_limits(tariff).get("features") or {}
    return bool(features.get(key, default))


def _monthly_limit_for_tariff(tariff: Optional[str]) -> int:
    return plan_limit(tariff, "monthly_posts", 300)


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
            return normalize_tariff(str(row[0] or "free"))
    finally:
        if own_conn:
            await release_db_connection(conn)


async def ensure_monthly_post_quota(user_id: int, *, conn: Any = None, units: int = 1) -> None:
    """Бросает QuotaExceededError, если лимит постов в месяц исчерпан.

    units — сколько sends планируется списать (multi-target job).
    """
    own_conn = conn is None
    if own_conn:
        conn = await get_db_connection()
    try:
        tariff = await get_user_tariff(user_id, conn=conn)
        limit = _monthly_limit_for_tariff(tariff)
        used = await count_user_posts_in_current_month(user_id, conn=conn)
        if used + max(0, units - 1) >= limit:
            raise QuotaExceededError(resource="monthly_posts", limit=limit, used=used)
    finally:
        if own_conn:
            await release_db_connection(conn)


async def ensure_smm_limit(user_id: int, key: str, used: int, *, units: int = 1) -> None:
    """Проверка числового лимита тарифа (own channels, brands, …)."""
    tariff = await get_user_tariff(user_id)
    limit = plan_limit(tariff, key, 0)
    if used + units > limit:
        raise QuotaExceededError(resource=key, limit=limit, used=used)


async def ensure_smm_feature(user_id: int, feature: str) -> None:
    tariff = await get_user_tariff(user_id)
    if not plan_feature(tariff, feature, False):
        raise QuotaExceededError(resource=f"feature:{feature}", limit=0, used=0)


async def ensure_ai_calls_quota(user_id: int, *, units: int = 1) -> None:
    """Increment and enforce monthly AI call quota (smm_ai_usage)."""
    tariff = await get_user_tariff(user_id)
    limit = plan_limit(tariff, "ai_calls_month", 0)
    if limit <= 0:
        raise QuotaExceededError(resource="ai_calls_month", limit=0, used=0)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO smm_ai_usage (user_id, month, calls)
                VALUES (%s, %s, 0)
                ON CONFLICT (user_id, month) DO NOTHING
                """,
                (user_id, month),
            )
            await cur.execute(
                "SELECT calls FROM smm_ai_usage WHERE user_id = %s AND month = %s",
                (user_id, month),
            )
            row = await cur.fetchone()
            used = int(row[0] if row else 0)
            if used + units > limit:
                raise QuotaExceededError(resource="ai_calls_month", limit=limit, used=used)
            await cur.execute(
                """
                UPDATE smm_ai_usage SET calls = calls + %s
                WHERE user_id = %s AND month = %s
                """,
                (units, user_id, month),
            )
    finally:
        await release_db_connection(conn)
