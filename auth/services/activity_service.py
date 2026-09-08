from typing import Any, Optional
from uuid import uuid4

from database import get_db_connection
from shared.billing.plan_definitions import normalize_tariff_code, paid_tariff_codes

IDLE_GAP_SECONDS = 300
MAX_CREDIT_SECONDS = 150


async def _user_tariff(user_id: int) -> str:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT tariff FROM users WHERE id = %s", (user_id,))
            row = await cur.fetchone()
    if not row or not row[0]:
        return "free"
    return normalize_tariff_code(str(row[0]))


async def record_auth_visit(user_id: int) -> None:
    """Фиксирует вход в сервис (логин/регистрация) без длительности сеанса."""
    tariff = await _user_tariff(user_id)
    session_id = f"auth-visit-{uuid4()}"
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_app_sessions (
                    user_id, client_session_id, tariff, started_at,
                    last_heartbeat_at, active_seconds, is_open
                )
                VALUES (%s, %s, %s, NOW(), NOW(), 0, FALSE)
                """,
                (user_id, session_id, tariff),
            )


async def record_session_heartbeat(user_id: int, client_session_id: str) -> None:
    """Продлевает активный сеанс или открывает новый, если пауза слишком длинная."""
    session_id = (client_session_id or "").strip()[:64]
    if len(session_id) < 8:
        return

    tariff = await _user_tariff(user_id)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_app_sessions
                SET is_open = FALSE
                WHERE user_id = %s
                  AND client_session_id = %s
                  AND is_open = TRUE
                  AND EXTRACT(EPOCH FROM (NOW() - last_heartbeat_at)) > %s
                """,
                (user_id, session_id, IDLE_GAP_SECONDS),
            )
            await cur.execute(
                """
                UPDATE user_app_sessions
                SET last_heartbeat_at = NOW(),
                    tariff = %s,
                    active_seconds = active_seconds + LEAST(
                        GREATEST(
                            EXTRACT(EPOCH FROM (NOW() - last_heartbeat_at))::INTEGER,
                            0
                        ),
                        %s
                    )
                WHERE id = (
                    SELECT id
                    FROM user_app_sessions
                    WHERE user_id = %s
                      AND client_session_id = %s
                      AND is_open = TRUE
                    ORDER BY last_heartbeat_at DESC
                    LIMIT 1
                )
                RETURNING id
                """,
                (tariff, MAX_CREDIT_SECONDS, user_id, session_id),
            )
            updated = await cur.fetchone()
            if updated:
                return
            await cur.execute(
                """
                INSERT INTO user_app_sessions (
                    user_id, client_session_id, tariff, started_at,
                    last_heartbeat_at, active_seconds, is_open
                )
                VALUES (%s, %s, %s, NOW(), NOW(), 0, TRUE)
                """,
                (user_id, session_id, tariff),
            )


def _ratio(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


async def get_product_metrics() -> dict[str, Any]:
    """Active Users, Engagement, Retention и Conversion за 30/60 дней."""
    paid_codes = tuple(paid_tariff_codes()) or ("__none__",)
    placeholders = ",".join(["%s"] * len(paid_codes))
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT
                    COUNT(DISTINCT user_id) FILTER (
                        WHERE last_heartbeat_at >= NOW() - INTERVAL '30 days'
                    ) AS active_30,
                    COUNT(DISTINCT user_id) FILTER (
                        WHERE last_heartbeat_at >= NOW() - INTERVAL '60 days'
                    ) AS active_60,
                    COALESCE(
                        SUM(active_seconds) FILTER (
                            WHERE last_heartbeat_at >= NOW() - INTERVAL '30 days'
                        ),
                        0
                    ) AS seconds_30,
                    COUNT(DISTINCT user_id) FILTER (
                        WHERE last_heartbeat_at >= NOW() - INTERVAL '30 days'
                          AND tariff IN ({placeholders})
                    ) AS paid_30,
                    COUNT(DISTINCT user_id) FILTER (
                        WHERE last_heartbeat_at >= NOW() - INTERVAL '60 days'
                          AND tariff IN ({placeholders})
                    ) AS paid_60
                FROM user_app_sessions
                """,
                paid_codes + paid_codes,
            )
            row = await cur.fetchone()

    active_30 = int(row[0] or 0) if row else 0
    active_60 = int(row[1] or 0) if row else 0
    seconds_30 = int(row[2] or 0) if row else 0
    paid_30 = int(row[3] or 0) if row else 0
    paid_60 = int(row[4] or 0) if row else 0
    engagement = round(seconds_30 / active_30, 2) if active_30 else 0.0

    return {
        "active_users_30d": active_30,
        "active_users_60d": active_60,
        "total_active_seconds_30d": seconds_30,
        "engagement_seconds": engagement,
        "retention": _ratio(active_30, active_60),
        "paid_active_users_30d": paid_30,
        "paid_active_users_60d": paid_60,
        "conversion": _ratio(paid_30, paid_60),
    }
