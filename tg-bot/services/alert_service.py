"""Мгновенная отправка алертов в Telegram при совпадении условий."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from telethon import events
from telethon.client import TelegramClient

from database import get_db_connection, release_db_connection
from .message_handler import MessageHandler

logger = logging.getLogger(__name__)

TG_MESSAGE_LIMIT = 4096

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore


def parse_channel(channel_to_post: Optional[str]) -> Optional[Any]:
    if not channel_to_post:
        return None
    channel = str(channel_to_post).strip()
    if not channel:
        return None
    if channel.startswith("@"):
        return channel
    try:
        return int(channel)
    except ValueError:
        return channel


async def build_alert_message(
    alert_text: str,
    chat_id: int,
    message_text: str,
    rule: Optional[Dict[str, Any]] = None,
) -> str:
    header = f"{alert_text.strip()}\n\nКанал: {chat_id}\nСообщение:\n"
    body = message_text or ""

    if rule and rule.get("include_ai_summary") and ai_client is not None and body:
        try:
            cached = await _get_cached_summary(body)
            if cached:
                summary = cached
            else:
                summary = await asyncio.wait_for(
                    ai_client.summarize(body, max_length=500),
                    timeout=3.0,
                )
                await _cache_summary(body, summary)
            body = f"Кратко: {summary}\n\n---\n{body}"
        except Exception as exc:
            logger.warning("AI summary skipped for alert: %s", exc)

    full = header + body
    if len(full) <= TG_MESSAGE_LIMIT:
        return full
    available = TG_MESSAGE_LIMIT - len(header) - 3
    if available <= 0:
        return full[: TG_MESSAGE_LIMIT - 3] + "..."
    return header + body[:available] + "..."


async def _get_cached_summary(text: str) -> Optional[str]:
    from services.event_logger import compute_text_hash

    text_hash = compute_text_hash(text)
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT summary FROM tg_summary_cache
                    WHERE text_hash = %s AND expires_at > CURRENT_TIMESTAMP
                    """,
                    (text_hash,),
                )
                row = await cur.fetchone()
                return row[0] if row else None
        finally:
            await release_db_connection(conn)
    except Exception:
        return None


async def _cache_summary(text: str, summary: str) -> None:
    from services.event_logger import compute_text_hash

    text_hash = compute_text_hash(text)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO tg_summary_cache (text_hash, summary, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (text_hash) DO UPDATE
                    SET summary = EXCLUDED.summary, expires_at = EXCLUDED.expires_at
                    """,
                    (text_hash, summary, expires_at),
                )
        finally:
            await release_db_connection(conn)
    except Exception as exc:
        logger.debug("Summary cache write failed: %s", exc)


def get_active_rules(profile: Dict) -> List[Dict]:
    if not profile.get("alert_enabled"):
        return []

    rules = profile.get("alert_rules") or []
    if not isinstance(rules, list):
        return []

    active: List[Dict] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if not rule.get("enabled", True):
            continue

        if not rule.get("id"):
            rule["id"] = str(uuid4())

        chats = [c.strip() for c in (rule.get("chats_to_read") or []) if isinstance(c, str) and c.strip()]
        conditions = [
            c.strip() for c in (rule.get("save_conditions") or []) if isinstance(c, str) and c.strip()
        ]
        channel = (rule.get("channel_to_post") or "").strip()
        alert_text = (rule.get("alert_text") or "").strip()

        if not chats or not conditions or not channel or not alert_text:
            continue

        active.append(
            {
                "id": rule.get("id"),
                "priority": int(rule.get("priority") or 0),
                "chats_to_read": chats,
                "save_conditions": conditions,
                "conditions_mode": rule.get("conditions_mode") or "any_of",
                "category_filter": rule.get("category_filter"),
                "channel_to_post": channel,
                "alert_text": alert_text,
                "dedup_window_sec": int(rule.get("dedup_window_sec") or 3600),
                "rate_limit_per_hour": rule.get("rate_limit_per_hour"),
                "time_windows": rule.get("time_windows") or [],
                "min_text_length": int(rule.get("min_text_length") or 0),
                "include_ai_summary": bool(rule.get("include_ai_summary")),
                "sentiment_filter": rule.get("sentiment_filter"),
                "tags": rule.get("tags") or [],
                "stop_on_match": bool(rule.get("stop_on_match")),
            }
        )

    return active


def chat_matches_rule(event: events.NewMessage.Event, rule: Dict, message_handler: MessageHandler) -> bool:
    return message_handler.chat_id_in_list(event.chat_id, rule.get("chats_to_read") or [])


def message_matches_conditions(
    event: events.NewMessage.Event,
    conditions: List[str],
    message_handler: MessageHandler,
) -> bool:
    if not conditions:
        return False
    matched, _ = message_handler.evaluate_conditions(event, conditions, conditions_mode="any_of")
    return matched


class AlertService:
    def __init__(self, message_handler: Optional[MessageHandler] = None):
        self.message_handler = message_handler or MessageHandler()

    async def send_alert(
        self,
        client: TelegramClient,
        rule: Dict,
        event: events.NewMessage.Event,
        message_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        channel = parse_channel(rule.get("channel_to_post"))
        if channel is None:
            logger.warning("Alert rule skipped: channel_to_post is empty")
            return False

        message_text = event.raw_text or event.message.message or ""
        text = await build_alert_message(
            rule.get("alert_text", ""),
            event.chat_id,
            message_text,
            rule=rule,
        )

        try:
            await client.send_message(channel, text)
            logger.info(
                "Sent alert to %s for chat %s (message %s)",
                channel,
                event.chat_id,
                event.message.id,
            )
            return True
        except Exception as exc:
            logger.error("Error sending alert to %s: %s", channel, exc, exc_info=True)
            return False
