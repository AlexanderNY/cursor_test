"""Обработка входящих сообщений Telegram."""

from __future__ import annotations

import logging
import re
from datetime import datetime, time as dt_time
from typing import Any, Dict, List, Optional

from telethon import events

logger = logging.getLogger(__name__)

REGEX_TIMEOUT_SEC = 0.1
MAX_REGEX_PATTERN_LEN = 200


class MessageHandler:
    """Обработчик сообщений Telegram."""

    @staticmethod
    def should_save_message(event: events.NewMessage.Event, save_conditions: List[str]) -> bool:
        if not save_conditions:
            return True
        matched, _ = MessageHandler.evaluate_conditions(
            event,
            save_conditions,
            conditions_mode="any_of",
        )
        return matched

    @staticmethod
    def evaluate_conditions(
        event: events.NewMessage.Event,
        conditions: List[str],
        conditions_mode: str = "any_of",
        category_filter: Optional[str] = None,
        message_metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, List[str]]:
        if category_filter:
            meta = message_metadata or {}
            if str(meta.get("category", "")).lower() != category_filter.lower():
                return False, []

        if not conditions:
            return False, []

        raw_text = event.raw_text or event.message.message or ""
        matched: List[str] = []

        if conditions_mode == "regex":
            for pattern in conditions:
                if MessageHandler._safe_regex(raw_text, pattern):
                    matched.append(pattern)
            return bool(matched), matched

        if conditions_mode == "all_of":
            for condition in conditions:
                if not condition or condition not in raw_text:
                    return False, []
                matched.append(condition)
            return True, matched

        for condition in conditions:
            if condition and condition in raw_text:
                matched.append(condition)
        return bool(matched), matched

    @staticmethod
    def _safe_regex(text: str, pattern: str) -> bool:
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            logger.warning("Invalid regex pattern: %s", pattern[:50])
            return False

    @staticmethod
    def is_within_time_windows(time_windows: List[Dict[str, Any]]) -> bool:
        if not time_windows:
            return True
        now = datetime.now().time()
        for window in time_windows:
            start_str = window.get("start")
            end_str = window.get("end")
            if not start_str:
                continue
            try:
                start_parts = [int(x) for x in start_str.split(":")]
                start = dt_time(start_parts[0], start_parts[1])
                if end_str:
                    end_parts = [int(x) for x in end_str.split(":")]
                    end = dt_time(end_parts[0], end_parts[1])
                    if start <= end:
                        if start <= now <= end:
                            return True
                    else:
                        if now >= start or now <= end:
                            return True
                else:
                    if now >= start:
                        return True
            except (ValueError, IndexError):
                continue
        return False

    @staticmethod
    async def extract_message_data(event: events.NewMessage.Event) -> Dict:
        message = event.message
        sender = await event.get_sender()
        text = message.message or ""
        return {
            "text": text,
            "raw_text": event.raw_text or "",
            "message_id": message.id,
            "date": message.date,
            "author_id": sender.id if sender else None,
            "author_username": getattr(sender, "username", None) if sender else None,
            "author_title": getattr(sender, "title", None) if sender else None,
            "chat_id": event.chat_id,
            "has_media": message.media is not None,
            "media": message.media,
        }

    @staticmethod
    def chat_ref_id(chat: Any) -> Optional[str]:
        """Извлекает ID из строки или {id, title}."""
        if chat is None:
            return None
        if isinstance(chat, dict):
            raw = chat.get("id") or chat.get("external_id") or chat.get("value")
            if raw is None:
                return None
            value = str(raw).strip()
            return value or None
        value = str(chat).strip()
        return value or None

    @staticmethod
    def get_chats_list(chats_to_read: List) -> List:
        if not chats_to_read:
            return []
        result = []
        for chat in chats_to_read:
            raw = MessageHandler.chat_ref_id(chat)
            if not raw:
                continue
            if isinstance(raw, str):
                try:
                    if raw.startswith("@"):
                        result.append(raw)
                    else:
                        result.append(int(raw))
                except ValueError:
                    result.append(raw)
            else:
                result.append(raw)
        return result

    @staticmethod
    def chat_id_in_list(chat_id: Optional[int], chats: List) -> bool:
        if chat_id is None:
            return False
        normalized = MessageHandler.get_chats_list(chats)
        for chat in normalized:
            try:
                if int(chat) == int(chat_id):
                    return True
            except (TypeError, ValueError):
                pass
            if str(chat) == str(chat_id):
                return True
        return False
