"""Append-only post lifecycle audit (not event sourcing)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


async def log_post_lifecycle_event(
    *,
    platform: str,
    post_id: int,
    to_status: str,
    from_status: Optional[str] = None,
    user_id: Optional[int] = None,
    job_id: Optional[int] = None,
    actor: str = "system",
    payload: Optional[dict[str, Any]] = None,
    conn: Any = None,
) -> None:
    """Best-effort insert into post_lifecycle_events. Never raises to callers."""
    owns_conn = conn is None
    try:
        if owns_conn:
            conn = await get_db_connection()
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO post_lifecycle_events
                    (platform, post_id, user_id, job_id, from_status, to_status, actor, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    platform,
                    post_id,
                    user_id,
                    job_id,
                    from_status,
                    to_status,
                    (actor or "system")[:80],
                    json.dumps(payload or {}),
                ),
            )
    except Exception as exc:
        logger.debug(
            "post_lifecycle_event skipped platform=%s post_id=%s: %s",
            platform,
            post_id,
            exc,
        )
    finally:
        if owns_conn and conn is not None:
            await release_db_connection(conn)
