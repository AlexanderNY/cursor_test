"""Сбор и сохранение постов в БД."""

import json
import logging
from typing import Dict, List, Optional
from telethon import events
from database import get_db_connection, release_db_connection
from config import settings


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class PostCollector:
    """Сервис для сохранения постов в tg_posts."""

    async def save_post(
        self,
        user_id: int,
        event: events.NewMessage.Event,
        images: List[str],
        profile: Dict
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
                author = getattr(sender, 'title', None) or getattr(sender, 'username', None)
                if author and isinstance(author, str):
                    author = author[:255]

            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_posts (
                            user_id, post_text, post_date, author,
                            images, status, post_type, domain,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, 'collected', 'tg', %s,
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
                        )
                    )

                    row = await cur.fetchone()
                    if row:
                        columns = [col.name for col in cur.description]
                        post = dict(zip(columns, row))

                        if isinstance(post.get('images'), str):
                            try:
                                post['images'] = json.loads(post['images'])
                            except (json.JSONDecodeError, TypeError):
                                post['images'] = []

                        _log_action("Saved post %s to tg_posts for user %s (msg_id=%s chat_id=%s)",
                                    post['id'], user_id, message.id, event.chat_id)
                        return post

            finally:
                await release_db_connection(conn)

        except Exception as e:
            logger.error(f"Error saving post for user {user_id}: {e}", exc_info=True)
            return None
