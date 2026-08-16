"""Сбор и сохранение постов в БД."""

import json
import logging
from typing import Dict, List, Optional

from telethon import events

from database import get_db_connection, release_db_connection
from config import settings
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
    """Сервис для сохранения постов в tg_posts."""

    async def save_post(
        self,
        user_id: int,
        event: events.NewMessage.Event,
        images: List[str],
        profile: Dict,
    ) -> Optional[Dict]:
        """Сохраняет пост в таблицу tg_posts со статусом collected.

        Args:
            user_id: ID пользователя
            event: Событие нового сообщения
            images: Список путей к изображениям
            profile: Профиль пользователя из БД

        Returns:
            Словарь с данными сохраненного поста или None в случае ошибки
        """
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
            target_channels = _target_channels_from_profile(profile)

            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_posts (
                            user_id, post_text, post_date, author,
                            images, status, post_type, domain,
                            to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram,
                            target_channels,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, 'collected', 'tg', %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s::jsonb,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        RETURNING *
                        """,
                        (
                            user_id,
                            post_text,
                            post_date,
                            author,
                            json.dumps(images),
                            domain,
                            dest["to_tg"],
                            dest["to_tw"],
                            dest["to_wp"],
                            dest["to_vk"],
                            dest["to_threads"],
                            dest["to_dzen"],
                            dest["to_instagram"],
                            json.dumps(target_channels),
                        ),
                    )

                    row = await cur.fetchone()
                    if row:
                        columns = [col.name for col in cur.description]
                        post = dict(zip(columns, row))

                        if isinstance(post.get("images"), str):
                            try:
                                post["images"] = json.loads(post["images"])
                            except (json.JSONDecodeError, TypeError):
                                post["images"] = []

                        if isinstance(post.get("target_channels"), str):
                            try:
                                post["target_channels"] = json.loads(post["target_channels"])
                            except (json.JSONDecodeError, TypeError):
                                post["target_channels"] = []

                        _log_action(
                            "Saved post %s to tg_posts for user %s (msg_id=%s chat_id=%s to_tg=%s targets=%s)",
                            post["id"],
                            user_id,
                            message.id,
                            event.chat_id,
                            dest["to_tg"],
                            target_channels,
                        )
                        return post

            finally:
                await release_db_connection(conn)

        except Exception as e:
            logger.error(f"Error saving post for user {user_id}: {e}", exc_info=True)
            return None
