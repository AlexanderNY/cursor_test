"""Журнал действий администратора."""

import json
from typing import Any, Optional

from database import get_db_connection


async def log_admin_audit(
    admin_user_id: int,
    action: str,
    *,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """Записывает событие в admin_audit_log."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO admin_audit_log
                    (admin_user_id, action, target_type, target_id, details_json)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (
                    admin_user_id,
                    action,
                    target_type,
                    target_id,
                    json.dumps(details) if details is not None else None,
                ),
            )


async def get_admin_audit_log(limit: int = 100) -> list[dict[str, Any]]:
    """Последние записи журнала (новые сверху)."""
    lim = max(1, min(limit, 500))
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, admin_user_id, action, target_type, target_id, details_json, created_at
                FROM admin_audit_log
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (lim,),
            )
            rows = await cur.fetchall()
    return [
        {
            "id": r[0],
            "admin_user_id": r[1],
            "action": r[2],
            "target_type": r[3],
            "target_id": r[4],
            "details_json": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]
