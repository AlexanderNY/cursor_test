"""Load SMM brand channels with discussion chats for comment ingest."""

from __future__ import annotations

import logging
from typing import Any

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


async def list_discussion_bindings() -> list[dict[str, Any]]:
    """Return {user_id, channel_id, discussion_id, brand_id} for TG channels with discussion."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT b.user_id, c.id, c.discussion_external_id, c.brand_id, c.external_id, c.title
                FROM smm_brand_channels c
                JOIN smm_brands b ON b.id = c.brand_id
                WHERE c.network = 'tg'
                  AND c.discussion_external_id IS NOT NULL
                  AND c.discussion_external_id != ''
                  AND COALESCE(c.comments_collect_enabled, FALSE) = TRUE
                """
            )
            rows = await cur.fetchall()
            result = []
            for r in rows:
                result.append(
                    {
                        "user_id": int(r[0]),
                        "channel_id": int(r[1]),
                        "discussion_id": str(r[2]).strip(),
                        "brand_id": int(r[3]) if r[3] is not None else None,
                        "channel_external_id": str(r[4]),
                        "title": r[5],
                    }
                )
            return result
    except Exception as exc:
        logger.debug("list_discussion_bindings failed (table may be missing): %s", exc)
        return []
    finally:
        await release_db_connection(conn)
