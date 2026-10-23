"""Internal notification inserts (no admin JWT)."""

from __future__ import annotations

import logging
from typing import Optional

from database import get_db_connection, release_db_connection
from services.notification_html import sanitize_notification_html

logger = logging.getLogger(__name__)


async def notify_user(
    user_id: int,
    message: str,
    *,
    type_: str = "publish",
) -> Optional[int]:
    """Insert a user-visible notification. Returns id or None on failure."""
    if not user_id or not (message or "").strip():
        return None
    safe = sanitize_notification_html((message or "").strip())
    if not safe:
        return None
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO notifications (message, user_id, type)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (safe, user_id, type_ or "general"),
                )
                row = await cur.fetchone()
                return int(row[0]) if row else None
        finally:
            await release_db_connection(conn)
    except Exception as exc:
        logger.warning("notify_user failed user_id=%s: %s", user_id, exc)
        return None
