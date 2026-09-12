"""Сбор и сохранение постов в БД."""

import json
import logging
from typing import Dict, List, Optional

from telethon import events

from database import get_db_connection, release_db_connection
from config import settings
from shared.db.bot_queue import dest_flags_to_platforms
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http
from .message_handler import MessageHandler


logger = logging.getLogger(__name__)

_PROCESS_SERVICE_TO_FLAG = {
    "telegram": "to_tg",
    "wordpress": "to_wp",
    "twitter": "to_tw",
    "vkontakte": "to_vk",
    "threads": "to_threads",
    "dzen": "to_dzen",
    "instagram": "to_instagram",
}


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def destination_flags_from_profile(profile: Dict) -> Dict[str, bool]:
    """Строит to_* флаги из process_services / сетей publish targets.

    Если сервисы не выбраны, но задан канал публикации — по умолчанию to_tg.
    """
    flags = {
        "to_tg": False,
        "to_tw": False,
        "to_wp": False,
        "to_vk": False,
        "to_threads": False,
        "to_dzen": False,
        "to_instagram": False,
    }
    services = profile.get("process_services") or []
    if isinstance(services, str):
        try:
            services = json.loads(services)
        except (json.JSONDecodeError, TypeError):
            services = []
    if not isinstance(services, list):
        services = []

    for item in services:
        key = _PROCESS_SERVICE_TO_FLAG.get(str(item).strip().lower())
        if key:
            flags[key] = True

    if any(flags.values()):
        return flags

    targets = profile.get("target_channels") or []
    if isinstance(targets, str):
        try:
            targets = json.loads(targets)
        except (json.JSONDecodeError, TypeError):
            targets = []
    if isinstance(targets, list) and any(
        MessageHandler.chat_ref_id(item) for item in targets
    ):
        flags["to_tg"] = True
        return flags

    has_channel = bool(
        MessageHandler.chat_ref_id(profile.get("channel_to_post"))
        or any(MessageHandler.chat_ref_id(item) for item in (profile.get("channels_to_post") or []))
    )
    if has_channel or profile.get("publish_enabled"):
        flags["to_tg"] = True
    return flags


def _target_channels_from_profile(profile: Dict) -> List[str]:
    raw = profile.get("target_channels") or []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raw = []
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        chat_id = MessageHandler.chat_ref_id(item)
        if chat_id:
            out.append(chat_id)
    return out


class PostCollector:
    """Сервис для сохранения входящих TG сообщений в posts."""

    async def save_post(
        self,
        user_id: int,
        event: events.NewMessage.Event,
        images: List[str],
        profile: Dict,
    ) -> Optional[Dict]:
        """Сохраняет пост в таблицу posts со статусом collected."""
        try:
            sender = await event.get_sender()
            message = event.message

            post_text = message.message or ""
            post_date = message.date
            author = None
            domain = str(event.chat_id) if event.chat_id else None

            if sender:
                author = getattr(sender, "title", None) or getattr(sender, "username", None)
                if author and isinstance(author, str):
                    author = author[:255]

            dest = destination_flags_from_profile(profile)
            platforms = dest_flags_to_platforms(dest) or ["tg"]
            target_channels = _target_channels_from_profile(profile)
            chat_id = event.chat_id
            native_id = f"{chat_id}:{message.id}" if chat_id is not None else str(message.id)

            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    repo = PostsRepository(cur)
                    created = await repo.create_inbound(
                        InboundPostCreate(
                            user_id=user_id,
                            source_platform="tg",
                            post_text=post_text,
                            post_date=post_date,
                            author=author,
                            domain=domain,
                            images=images,
                            extras={
                                "metadata": {
                                    "telegram_message_id": message.id,
                                    "telegram_chat_id": str(chat_id) if chat_id is not None else None,
                                }
                            },
                            source_native_id=native_id,
                            target_channels=target_channels,
                            target_platforms=platforms or ("tg",),
                            target_status="pending",
                            status="collected",
                        )
                    )
                    post = {
                        **created,
                        "post_text": post_text,
                        "images": images,
                        "target_channels": target_channels,
                    }
                    _log_action(
                        "Saved post %s to posts for user %s (msg_id=%s chat_id=%s platforms=%s targets=%s)",
                        post["id"],
                        user_id,
                        message.id,
                        event.chat_id,
                        platforms,
                        target_channels,
                    )
            finally:
                await release_db_connection(conn)
            await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
            return post

        except Exception as e:
            logger.error(f"Error saving post for user {user_id}: {e}", exc_info=True)
            return None
