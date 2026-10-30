"""Запись циклов в service_cycle_log (общий хелпер для сервисов с context-manager DB)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def purge_old_cycle_logs(cur: Any, *, keep_days: int = 30, batch: int = 500) -> None:
    """Delete a batch of cycle-log rows older than keep_days."""
    await cur.execute(
        """
        DELETE FROM service_cycle_log
        WHERE id IN (
            SELECT id FROM service_cycle_log
            WHERE created_at < NOW() - (%s * INTERVAL '1 day')
            LIMIT %s
        )
        """,
        (int(keep_days), int(batch)),
    )


async def write_cycle_log(
    get_db_connection: Any,
    *,
    service_name: str,
    cycle_type: str,
    status: str = "ok",
    detail: Optional[str] = None,
    items_processed: int = 0,
) -> None:
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO service_cycle_log (
                        service_name, cycle_type, status, detail, items_processed
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        service_name,
                        cycle_type,
                        status,
                        (detail or "")[:2000] or None,
                        int(items_processed or 0),
                    ),
                )
                await purge_old_cycle_logs(cur)
    except Exception as exc:
        logger.debug("service_cycle_log skip (%s/%s): %s", service_name, cycle_type, exc)
