"""Гранты повышенного тарифа и возврат на free после expires_at.

Источник истины для пользователей, у которых есть строки в user_entitlements.
Если строк нет, users.tariff не меняется.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from database import get_db_connection
from services.auth_service import get_user_by_id, update_user_role_tariff
from shared.billing.entitlements import (
    PAID_GRANT_DAYS,
    grant_expires_at,
    resolve_effective_tariff,
)
from shared.billing.plan_definitions import normalize_tariff_code

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _row_grant(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "tariff": row[1],
        "source": row[2],
        "source_ref": row[3],
        "starts_at": row[4],
        "expires_at": row[5],
        "status": row[6],
    }


async def _expire_user(user_id: int, now: datetime) -> None:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_entitlements
                SET status = 'expired'
                WHERE user_id = %s AND status = 'active' AND expires_at <= %s
                """,
                (user_id, now),
            )


async def list_active_grants(user_id: int) -> list[dict[str, Any]]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, tariff, source, source_ref, starts_at, expires_at, status
                FROM user_entitlements
                WHERE user_id = %s AND status = 'active'
                ORDER BY expires_at DESC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
    return [_row_grant(row) for row in rows]


async def _has_any_grant(user_id: int) -> bool:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM user_entitlements WHERE user_id = %s LIMIT 1",
                (user_id,),
            )
            return await cur.fetchone() is not None


async def _write_period(user_id: int, status: Optional[str], period_end: Optional[datetime]) -> None:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE users SET
                    subscription_status = %s,
                    subscription_current_period_end = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, period_end, user_id),
            )


async def sync_user_tariff(
    user_id: int,
    *,
    changed_by_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Истечь просроченные гранты и записать эффективный тариф в users."""
    now = _now()
    await _expire_user(user_id, now)
    user = await get_user_by_id(user_id)
    if not user:
        return {
            "tariff": "free",
            "tariff_expires_at": None,
            "subscription_status": None,
            "entitlements": [],
            "changed": False,
        }
    if not await _has_any_grant(user_id):
        return {
            "tariff": normalize_tariff_code(user.get("tariff")),
            "tariff_expires_at": user.get("subscription_current_period_end"),
            "subscription_status": user.get("subscription_status"),
            "entitlements": [],
            "changed": False,
        }

    grants = await list_active_grants(user_id)
    tariff, expires_at = resolve_effective_tariff(grants)
    current = normalize_tariff_code(user.get("tariff"))
    changed = current != tariff
    if changed:
        await update_user_role_tariff(
            user_id=user_id,
            tariff=tariff,
            changed_by_user_id=changed_by_user_id,
        )
    status = "active" if tariff != "free" else "expired"
    await _write_period(user_id, status, expires_at)
    return {
        "tariff": tariff,
        "tariff_expires_at": expires_at,
        "subscription_status": status,
        "entitlements": grants,
        "changed": changed,
    }


async def upsert_grant(
    *,
    user_id: int,
    tariff: str,
    source: str,
    source_ref: Optional[str],
    days: int,
    changed_by_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Заменяет активный грант того же источника и пересчитывает тариф."""
    code = normalize_tariff_code(tariff)
    if code not in ("standard", "full"):
        raise ValueError("Грант выдаётся только на standard или full")
    if source not in ("payment", "promo"):
        raise ValueError("Источник гранта: payment или promo")
    now = _now()
    expires_at = grant_expires_at(now, days)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_entitlements
                SET status = 'revoked'
                WHERE user_id = %s AND source = %s AND status = 'active'
                """,
                (user_id, source),
            )
            await cur.execute(
                """
                INSERT INTO user_entitlements (
                    user_id, tariff, source, source_ref, starts_at, expires_at, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
                """,
                (user_id, code, source, source_ref, now, expires_at),
            )
    return await sync_user_tariff(user_id, changed_by_user_id=changed_by_user_id)


async def grant_payment(
    *,
    user_id: int,
    tariff: str,
    request_id: int,
    changed_by_user_id: Optional[int] = None,
) -> dict[str, Any]:
    return await upsert_grant(
        user_id=user_id,
        tariff=tariff,
        source="payment",
        source_ref=str(request_id),
        days=PAID_GRANT_DAYS,
        changed_by_user_id=changed_by_user_id,
    )


async def expire_due_grants() -> int:
    """Пометить просроченные гранты и вернуть затронутых пользователей на актуальный тариф."""
    now = _now()
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_entitlements
                SET status = 'expired'
                WHERE status = 'active' AND expires_at <= %s
                RETURNING user_id
                """,
                (now,),
            )
            rows = await cur.fetchall()
    user_ids = {int(row[0]) for row in rows}
    for user_id in user_ids:
        try:
            await sync_user_tariff(user_id)
        except Exception:
            logger.exception("entitlement sync failed for user %s", user_id)
    return len(user_ids)
