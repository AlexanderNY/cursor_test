"""Запись циклов в service_cycle_log (общий хелпер для сервисов с context-manager DB)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
    except Exception as exc:
        logger.debug("service_cycle_log skip (%s/%s): %s", service_name, cycle_type, exc)
