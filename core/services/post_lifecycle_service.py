"""Append-only post lifecycle audit (not event sourcing)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from database import get_db_connection, release_db_connection
from shared.db.post_lifecycle import insert_lifecycle_event

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
            await insert_lifecycle_event(
                cur,
                platform=platform,
                post_id=post_id,
                to_status=to_status,
                from_status=from_status,
                user_id=user_id,
                job_id=job_id,
                actor=actor,
                payload=payload,
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
