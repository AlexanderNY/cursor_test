"""Журнал событий VKontakte (vk_events) — зеркало tg_events."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

TEXT_PREVIEW_LIMIT = 500
RETENTION_DAYS = 90


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def compute_text_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def build_text_preview(text: str) -> str:
    if not text:
        return ""
    if len(text) <= TEXT_PREVIEW_LIMIT:
        return text
    return text[:TEXT_PREVIEW_LIMIT]


class EventLogger:
    """Запись событий в vk_events без падения основного потока."""

    async def log_event(
        self,
        user_id: int,
        event_type: str,
        *,
        owner_id: Optional[int] = None,
        post_id: Optional[int] = None,
        text: str = "",
        rule_id: Optional[str] = None,
        matched_conditions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO vk_events (
                            user_id, owner_id, post_id, event_type,
                            rule_id, matched_conditions, text_hash, text_preview, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            owner_id,
                            post_id,
                            event_type,
                            rule_id,
                            json.dumps(matched_conditions or []),
                            compute_text_hash(text or ""),
                            build_text_preview(text or ""),
                            json.dumps(metadata or {}),
                        ),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to log vk_event %s: %s", event_type, exc, exc_info=True)

    async def cleanup_old_events(self) -> int:
        cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM vk_events WHERE created_at < %s",
                        (cutoff,),
                    )
                    return cur.rowcount or 0
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to cleanup old vk_events: %s", exc)
            return 0
