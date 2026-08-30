"""Shared monthly AI-calls quota (smm_ai_usage), usable from core and tg-bot."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

AcquireConn = Callable[[], Awaitable[Any]]
ReleaseConn = Callable[[Any], Awaitable[None]]

_TARIFF_ALIASES = {"basic": "standard", "premium": "full"}

_AI_CALLS_MONTH: dict[str, int] = {
    "free": 0,
    "standard": 100,
    "full": 2000,
}


class AiQuotaExceeded(Exception):
    def __init__(self, *, resource: str, limit: int, used: int) -> None:
        self.resource = resource
        self.limit = limit
        self.used = used
        super().__init__(f"AI quota exceeded: {used}/{limit}")


def normalize_tariff(tariff: Optional[str]) -> str:
    t = (tariff or "free").strip().lower()
    return _TARIFF_ALIASES.get(t, t)


def ai_calls_limit(tariff: Optional[str]) -> int:
    return int(_AI_CALLS_MONTH.get(normalize_tariff(tariff), 0))


async def consume_ai_calls(
    user_id: int,
    *,
    units: int = 1,
    acquire: AcquireConn,
    release: ReleaseConn,
) -> None:
    """Increment smm_ai_usage; raise AiQuotaExceeded when over limit."""
    if units <= 0:
        return

    conn = await acquire()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT tariff FROM users WHERE id = %s", (user_id,))
            row = await cur.fetchone()
            tariff = normalize_tariff(str(row[0]) if row else "free")
            limit = ai_calls_limit(tariff)
            if limit <= 0:
                raise AiQuotaExceeded(resource="ai_calls_month", limit=0, used=0)

            month = datetime.now(timezone.utc).strftime("%Y-%m")
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
            used_row = await cur.fetchone()
            used = int(used_row[0] if used_row else 0)
            if used + units > limit:
                raise AiQuotaExceeded(resource="ai_calls_month", limit=limit, used=used)
            await cur.execute(
                """
                UPDATE smm_ai_usage SET calls = calls + %s
                WHERE user_id = %s AND month = %s
                """,
                (units, user_id, month),
            )
    finally:
        await release(conn)


async def read_ai_usage(
    user_id: int,
    *,
    acquire: AcquireConn,
    release: ReleaseConn,
    tariff: Optional[str] = None,
) -> dict[str, Any]:
    """Read-only monthly AI usage meter."""
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    used = 0
    resolved_tariff = normalize_tariff(tariff) if tariff is not None else None

    conn = await acquire()
    try:
        async with conn.cursor() as cur:
            if resolved_tariff is None:
                await cur.execute("SELECT tariff FROM users WHERE id = %s", (user_id,))
                row = await cur.fetchone()
                resolved_tariff = normalize_tariff(str(row[0]) if row else "free")
            await cur.execute(
                "SELECT calls FROM smm_ai_usage WHERE user_id = %s AND month = %s",
                (user_id, period),
            )
            used_row = await cur.fetchone()
            if used_row:
                used = int(used_row[0] or 0)
    finally:
        await release(conn)

    limit = ai_calls_limit(resolved_tariff)
    remaining = max(0, limit - used) if limit > 0 else 0
    return {
        "used": used,
        "limit": limit,
        "period": period,
        "remaining": remaining,
    }
