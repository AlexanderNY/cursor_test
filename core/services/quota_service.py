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
        "storage_gb": 1,
        "max_own_channels": 3,
        "max_brands": 1,
        "max_targets_per_job": 1,
        "max_automations": 0,
        "max_templates": 5,
        "max_media_packs": 2,
        "max_team_seats": 1,
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
        "storage_gb": 10,
        "max_own_channels": 10,
        "max_brands": 5,
        "max_targets_per_job": 5,
        "max_automations": 5,
        "max_templates": 50,
        "max_media_packs": 20,
        "max_team_seats": 5,
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
        "storage_gb": 100,
        "max_own_channels": 20,
        "max_brands": 20,
        "max_targets_per_job": 20,
        "max_automations": 50,
        "max_templates": 500,
        "max_media_packs": 100,
        "max_team_seats": 20,
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
    from shared.ai_quota import AiQuotaExceeded, consume_ai_calls

    try:
        await consume_ai_calls(
            user_id,
            units=units,
            acquire=get_db_connection,
            release=release_db_connection,
        )
    except AiQuotaExceeded as exc:
        raise QuotaExceededError(
            resource=exc.resource, limit=exc.limit, used=exc.used
        ) from exc


async def get_ai_usage(user_id: int) -> dict[str, Any]:
    """Read-only monthly AI usage for UI meter."""
    from shared.ai_quota import read_ai_usage

    tariff = await get_user_tariff(user_id)
    return await read_ai_usage(
        user_id,
        acquire=get_db_connection,
        release=release_db_connection,
        tariff=tariff,
    )


async def get_usage_summary(user_id: int) -> dict[str, Any]:
    """Агрегат used/limit для billing UI и QuotaBanner."""
    tariff = await get_user_tariff(user_id)
    limits = get_plan_limits(tariff)
    posts_used = await count_user_posts_in_current_month(user_id)
    ai = await get_ai_usage(user_id)

    channels_used = 0
    brands_used = 0
    automations_used = 0
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM smm_brand_channels c
                JOIN smm_brands b ON b.id = c.brand_id
                WHERE b.user_id = %s AND c.role = 'own'
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            channels_used = int(row[0] if row else 0)

            await cur.execute(
                "SELECT COUNT(*) FROM smm_brands WHERE user_id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            brands_used = int(row[0] if row else 0)

            await cur.execute(
                "SELECT COUNT(*) FROM smm_automations WHERE user_id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
            automations_used = int(row[0] if row else 0)
    finally:
        await release_db_connection(conn)

    def _metric(key: str, used: int | None, limit: int, *, unit: str = "") -> dict[str, Any]:
        return {
            "key": key,
            "used": used,
            "limit": limit,
            "unit": unit,
            "remaining": max(0, limit - (used or 0)) if used is not None and limit > 0 else None,
        }

    metrics = [
        _metric("monthly_posts", posts_used, int(limits.get("monthly_posts", 0))),
        _metric("ai_calls_month", int(ai.get("used", 0)), int(ai.get("limit", 0))),
        _metric("max_own_channels", channels_used, int(limits.get("max_own_channels", 0))),
        _metric("max_brands", brands_used, int(limits.get("max_brands", 0))),
        _metric("max_automations", automations_used, int(limits.get("max_automations", 0))),
        _metric("storage_gb", None, int(limits.get("storage_gb", 0)), unit="GB"),
    ]
    return {
        "tariff": tariff,
        "period": ai.get("period"),
        "features": limits.get("features") or {},
        "metrics": metrics,
    }
