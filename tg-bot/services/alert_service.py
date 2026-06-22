"""Мгновенная отправка алертов в Telegram при совпадении условий."""

import logging
from typing import Any, Dict, List, Optional

from telethon import events
from telethon.client import TelegramClient

from .message_handler import MessageHandler


logger = logging.getLogger(__name__)

TG_MESSAGE_LIMIT = 4096


def parse_channel(channel_to_post: Optional[str]) -> Optional[Any]:
    """Преобразует channel_to_post в формат для send_message."""
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


def build_alert_message(alert_text: str, chat_id: int, message_text: str) -> str:
    """Формирует текст оповещения по шаблону."""
    header = f"{alert_text.strip()}\n\nКанал: {chat_id}\nСообщение:\n"
    body = message_text or ""
    full = header + body
    if len(full) <= TG_MESSAGE_LIMIT:
        return full
    available = TG_MESSAGE_LIMIT - len(header) - 3
    if available <= 0:
        return full[: TG_MESSAGE_LIMIT - 3] + "..."
    return header + body[:available] + "..."


def get_active_rules(profile: Dict) -> List[Dict]:
    """Возвращает активные правила алертинга из профиля."""
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
                "chats_to_read": chats,
                "save_conditions": conditions,
                "channel_to_post": channel,
                "alert_text": alert_text,
            }
        )

    return active


def chat_matches_rule(event: events.NewMessage.Event, rule: Dict, message_handler: MessageHandler) -> bool:
    """Проверяет, что сообщение пришло из чата, указанного в правиле."""
    chat_id = event.chat_id
    if chat_id is None:
        return False

    normalized_chats = message_handler.get_chats_list(rule.get("chats_to_read") or [])
    for chat in normalized_chats:
        try:
            if int(chat) == int(chat_id):
                return True
        except (TypeError, ValueError):
            pass
        if str(chat) == str(chat_id):
            return True
    return False


def message_matches_conditions(
    event: events.NewMessage.Event,
    conditions: List[str],
    message_handler: MessageHandler,
) -> bool:
    """Проверяет совпадение текста сообщения с save_conditions."""
    if not conditions:
        return False
    return message_handler.should_save_message(event, conditions)


class AlertService:
    """Отправка алертов в каналы оповещения."""

    def __init__(self, message_handler: Optional[MessageHandler] = None):
        self.message_handler = message_handler or MessageHandler()

    async def send_alert(
        self,
        client: TelegramClient,
        rule: Dict,
        event: events.NewMessage.Event,
    ) -> bool:
        """Отправляет алерт в channel_to_post правила."""
        channel = parse_channel(rule.get("channel_to_post"))
        if channel is None:
            logger.warning("Alert rule skipped: channel_to_post is empty")
            return False

        message_text = event.raw_text or event.message.message or ""
        text = build_alert_message(rule.get("alert_text", ""), event.chat_id, message_text)

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
