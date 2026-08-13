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
    """Строит to_* флаги из process_services профиля.

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

    has_channel = bool(
        MessageHandler.chat_ref_id(profile.get("channel_to_post"))
        or any(MessageHandler.chat_ref_id(item) for item in (profile.get("channels_to_post") or []))
    )
    if has_channel or profile.get("publish_enabled"):
        flags["to_tg"] = True
    return flags


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

            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_posts (
                            user_id, post_text, post_date, author,
                            images, status, post_type, domain,
                            to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, 'collected', 'tg', %s,
                            %s, %s, %s, %s, %s, %s, %s,
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

                        _log_action(
                            "Saved post %s to tg_posts for user %s (msg_id=%s chat_id=%s to_tg=%s)",
                            post["id"],
                            user_id,
                            message.id,
                            event.chat_id,
                            dest["to_tg"],
                        )
                        return post

            finally:
                await release_db_connection(conn)

        except Exception as e:
            logger.error(f"Error saving post for user {user_id}: {e}", exc_info=True)
            return None
