"""Журнал событий Telegram (tg_events)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from telethon import events

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

TEXT_PREVIEW_LIMIT = 500
RETENTION_DAYS = 90


def normalize_text(text: str) -> str:
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text.strip().lower())
    return collapsed


def compute_text_hash(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_text_preview(text: str) -> str:
    if not text:
        return ""
    if len(text) <= TEXT_PREVIEW_LIMIT:
        return text
    return text[:TEXT_PREVIEW_LIMIT]


class EventLogger:
    """Запись событий в tg_events без блокировки основного потока."""

    async def log_event(
        self,
        user_id: int,
        event_type: str,
        event: events.NewMessage.Event,
        rule_id: Optional[str] = None,
        matched_conditions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        message_text = event.raw_text or event.message.message or ""
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_events (
                            user_id, chat_id, message_id, event_type,
                            rule_id, matched_conditions, text_hash, text_preview, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            event.chat_id,
                            event.message.id,
                            event_type,
                            rule_id,
                            json.dumps(matched_conditions or []),
                            compute_text_hash(message_text),
                            build_text_preview(message_text),
                            json.dumps(metadata or {}),
                        ),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to log tg_event %s: %s", event_type, exc, exc_info=True)

    async def cleanup_expired_dedup(self) -> int:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM tg_dedup_cache WHERE expires_at < CURRENT_TIMESTAMP"
                    )
                    deleted = cur.rowcount or 0
                    await cur.execute(
                        "DELETE FROM tg_summary_cache WHERE expires_at < CURRENT_TIMESTAMP"
                    )
                    return deleted
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to cleanup dedup cache: %s", exc)
            return 0

    async def cleanup_old_events(self) -> int:
        cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM tg_events WHERE created_at < %s",
                        (cutoff,),
                    )
                    return cur.rowcount or 0
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to cleanup old tg_events: %s", exc)
            return 0
