"""Движок умной маршрутизации алертов."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from telethon import events
from telethon.client import TelegramClient

from database import get_db_connection, release_db_connection
from services.event_logger import EventLogger, compute_text_hash
from services.message_handler import MessageHandler
from services.alert_service import AlertService, get_active_rules

logger = logging.getLogger(__name__)

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore


class RoutingEngine:
    """Многоуровневая маршрутизация алертов с dedup и rate limit."""

    def __init__(
        self,
        message_handler: Optional[MessageHandler] = None,
        alert_service: Optional[AlertService] = None,
        event_logger: Optional[EventLogger] = None,
    ):
        self.message_handler = message_handler or MessageHandler()
        self.alert_service = alert_service or AlertService(self.message_handler)
        self.event_logger = event_logger or EventLogger()

    async def process(
        self,
        client: TelegramClient,
        user_id: int,
        profile: Dict[str, Any],
        event: events.NewMessage.Event,
        message_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        if not profile.get("alert_enabled"):
            return 0

        rules = get_active_rules(profile)
        if not rules:
            return 0

        message_text = event.raw_text or event.message.message or ""
        if not message_text and not event.message.media:
            return 0

        text_hash = compute_text_hash(message_text)
        sent_count = 0

        sorted_rules = sorted(rules, key=lambda r: int(r.get("priority", 0)), reverse=True)

        for rule in sorted_rules:
            if not self._chat_matches(event, rule):
                continue

            time_windows = rule.get("time_windows") or []
            if time_windows and not self.message_handler.is_within_time_windows(time_windows):
                continue

            min_len = int(rule.get("min_text_length") or 0)
            if len(message_text) < min_len:
                continue

            conditions_mode = rule.get("conditions_mode") or "any_of"
            matched, matched_conditions = self.message_handler.evaluate_conditions(
                event,
                rule.get("save_conditions") or [],
                conditions_mode=conditions_mode,
                category_filter=rule.get("category_filter"),
                message_metadata=message_metadata,
            )
            if not matched:
                continue

            sentiment_filter = rule.get("sentiment_filter")
            if sentiment_filter and ai_client is not None:
                try:
                    sentiment_result = await asyncio.wait_for(
                        ai_client.sentiment(message_text),
                        timeout=2.0,
                    )
                    if sentiment_result.sentiment != sentiment_filter:
                        await self.event_logger.log_event(
                            user_id,
                            "alert_suppressed",
                            event,
                            rule_id=rule.get("id"),
                            matched_conditions=matched_conditions,
                            metadata={"reason": "sentiment_filter", "sentiment": sentiment_result.sentiment},
                        )
                        continue
                except Exception as exc:
                    logger.warning("Sentiment check failed, skipping filter: %s", exc)

            await self.event_logger.log_event(
                user_id,
                "alert_matched",
                event,
                rule_id=rule.get("id"),
                matched_conditions=matched_conditions,
            )

            if await self._is_duplicate(user_id, rule, event, text_hash):
                await self.event_logger.log_event(
                    user_id,
                    "alert_suppressed",
                    event,
                    rule_id=rule.get("id"),
                    matched_conditions=matched_conditions,
                    metadata={"reason": "dedup"},
                )
                continue

            if await self._rate_limit_exceeded(user_id, rule):
                await self.event_logger.log_event(
                    user_id,
                    "alert_suppressed",
                    event,
                    rule_id=rule.get("id"),
                    matched_conditions=matched_conditions,
                    metadata={"reason": "rate_limit"},
                )
                continue

            sent = await self.alert_service.send_alert(client, rule, event, message_metadata=message_metadata)
            if sent:
                await self._record_dedup(user_id, rule, event, text_hash)
                await self.event_logger.log_event(
                    user_id,
                    "alert_sent",
                    event,
                    rule_id=rule.get("id"),
                    matched_conditions=matched_conditions,
                    metadata={
                        "channel": (rule.get("channel_to_post") or "").strip(),
                        "channel_title": rule.get("channel_to_post_title"),
                        "source_chat_id": event.chat_id,
                    },
                )
                sent_count += 1

            if rule.get("stop_on_match"):
                break

        return sent_count

    def _chat_matches(self, event: events.NewMessage.Event, rule: Dict[str, Any]) -> bool:
        return self.message_handler.chat_id_in_list(
            event.chat_id,
            rule.get("chats_to_read") or [],
        )

    async def _is_duplicate(
        self,
        user_id: int,
        rule: Dict[str, Any],
        event: events.NewMessage.Event,
        text_hash: str,
    ) -> bool:
        window_sec = int(rule.get("dedup_window_sec") or 3600)
        if window_sec <= 0:
            return False

        channel = (rule.get("channel_to_post") or "").strip()
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT 1 FROM tg_dedup_cache
                        WHERE user_id = %s AND text_hash = %s AND chat_id = %s
                          AND expires_at > CURRENT_TIMESTAMP
                          AND (channel_to_post = %s OR channel_to_post IS NULL)
                        LIMIT 1
                        """,
                        (user_id, text_hash, event.chat_id, channel or None),
                    )
                    row = await cur.fetchone()
                    return row is not None
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Dedup check failed: %s", exc)
            return False

    async def _record_dedup(
        self,
        user_id: int,
        rule: Dict[str, Any],
        event: events.NewMessage.Event,
        text_hash: str,
    ) -> None:
        window_sec = int(rule.get("dedup_window_sec") or 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=window_sec)
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_dedup_cache (
                            user_id, text_hash, chat_id, rule_id, channel_to_post, expires_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            text_hash,
                            event.chat_id,
                            rule.get("id"),
                            rule.get("channel_to_post"),
                            expires_at,
                        ),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to record dedup: %s", exc)

    async def _rate_limit_exceeded(self, user_id: int, rule: Dict[str, Any]) -> bool:
        limit = rule.get("rate_limit_per_hour")
        if not limit:
            return False
        rule_id = rule.get("id")
        if not rule_id:
            return False
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT COUNT(*) FROM tg_events
                        WHERE user_id = %s AND rule_id = %s
                          AND event_type = 'alert_sent'
                          AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                        """,
                        (user_id, rule_id),
                    )
                    row = await cur.fetchone()
                    count = row[0] if row else 0
                    return count >= int(limit)
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Rate limit check failed: %s", exc)
            return False


def ensure_rule_ids(profile: Dict[str, Any]) -> None:
    """Добавляет stable id правилам без id (backward compat)."""
    rules = profile.get("alert_rules") or []
    if not isinstance(rules, list):
        return
    for rule in rules:
        if isinstance(rule, dict) and not rule.get("id"):
            rule["id"] = str(uuid4())
