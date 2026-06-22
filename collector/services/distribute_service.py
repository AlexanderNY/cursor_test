"""Фаза 2: Распределение обработанных постов из posts обратно в платформенные таблицы."""

import json
import logging
from datetime import datetime
from typing import Any

from database import get_db_connection
from config import settings, TARGET_TABLES

logger = logging.getLogger(__name__)

# Колонки для вставки в целевую *_posts таблицу (posts.to_dzen, to_instagram и posts.videos — в миграциях)
_POST_COLUMNS = [
    "user_id", "domain", "url", "title", "author", "avatar",
    "post_date", "post_text", "screenshot", "images", "image_over_text",
    "comments", "reposts", "likes", "views", "is_ad", "status",
    "post_type", "to_tg", "to_tw", "to_wp", "to_vk", "to_dzen", "to_instagram",
    "to_threads",
]

# Все флаги to_* для проверки
_TARGET_FLAGS = list(TARGET_TABLES.keys())

# Ключи в platform_texts (из processor) для каждой целевой платформы
_PLATFORM_TEXT_KEYS = {"tg": "telegram", "wp": "wordpress", "vk": "vkontakte", "dzen": "dzen", "instagram": "instagram"}


class DistributeService:
    """Сервис распределения постов из posts -> *_posts."""

    def __init__(self) -> None:
        self.last_run_at: datetime | None = None
        self.total_distributed: int = 0
        self.last_cycle_distributed: int = 0

    async def run_distribute_cycle(self) -> int:
        """Выполняет один цикл распределения.

        1. SELECT из posts WHERE status = 'ready' FOR UPDATE SKIP LOCKED
        2. Для каждого поста проверить флаги to_tg, to_wp, ...
        3. INSERT в целевые *_posts таблицы со статусом 'ready'
        4. UPDATE posts SET status = 'distributed'

        Returns:
            Количество распределённых постов за цикл.
        """
        batch_size = settings.DISTRIBUTE_BATCH_SIZE

        async with get_db_connection() as conn:
            cur = await conn.cursor()
            try:
                await cur.execute("BEGIN")

                # 1. Выбрать готовые посты (включая platform_texts и videos для dzen)
                select_cols = (
                    ["id", "source_platform", "source_id"] + _POST_COLUMNS + ["platform_texts", "videos"]
                )
                col_str = ", ".join(select_cols)

                await cur.execute(
                    f"""
                    SELECT {col_str}
                    FROM posts
                    WHERE status = 'ready'
                    ORDER BY created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (batch_size,),
                )
                rows = await cur.fetchall()

                if not rows:
                    await cur.execute("COMMIT")
                    self.last_run_at = datetime.utcnow()
                    self.last_cycle_distributed = 0
                    return 0

                distributed_ids: list[int] = []

                for row in rows:
                    record = dict(zip(select_cols, row))
                    post_id = record["id"]
                    source_platform = record.get("source_platform")

                    distributed_ids.append(post_id)

                    # 2. Проверить каждый целевой флаг
                    for flag, target_info in TARGET_TABLES.items():
                        target_platform = target_info["platform"]
                        target_table = target_info["table"]

                        # Пропустить, если флаг не установлен
                        if not record.get(flag):
                            continue

                        # Одна и та же платформа: пост из tg_posts обработан — обновить запись в tg_posts до ready
                        if target_platform == source_platform:
                            await self._update_same_platform_target(
                                cur, target_table, record, target_platform
                            )
                            continue

                        # 3. Вставить в целевую таблицу (пост уходит в другую платформу)
                        await self._insert_into_target(
                            cur, target_table, record
                        )

                # 4. Обновить статус в posts
                if distributed_ids:
                    ids_placeholder = ", ".join(
                        ["%s"] * len(distributed_ids)
                    )
                    await cur.execute(
                        f"""
                        UPDATE posts
                        SET status = 'distributed', updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({ids_placeholder})
                        """,
                        distributed_ids,
                    )

                await cur.execute("COMMIT")

                count = len(distributed_ids)
                self.last_run_at = datetime.utcnow()
                self.last_cycle_distributed = count
                self.total_distributed += count

                if count > 0:
                    logger.info("Distribute cycle done: %d posts", count)

                return count

            except Exception:
                await cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

    async def _update_same_platform_target(
        self,
        cur: Any,
        target_table: str,
        record: dict[str, Any],
        target_platform: str,
    ) -> None:
        """Обновляет существующую запись в платформенной таблице до status='ready'.

        Используется, когда пост собран из tg_posts и после обработки снова
        публикуется в Telegram: обновляем ту же строку tg_posts (id=source_id).
        """
        source_id = record.get("source_id")
        user_id = record.get("user_id")
        if source_id is None or user_id is None:
            logger.warning(
                "Cannot update same-platform: source_id=%s user_id=%s",
                source_id,
                user_id,
            )
            return

        # Текст для платформы из platform_texts (ключи: telegram, wordpress, vkontakte)
        post_text = record.get("post_text") or ""
        platform_key = _PLATFORM_TEXT_KEYS.get(target_platform, target_platform)
        platform_texts_raw = record.get("platform_texts")
        if platform_texts_raw:
            try:
                texts = (
                    json.loads(platform_texts_raw)
                    if isinstance(platform_texts_raw, str)
                    else platform_texts_raw
                )
                if isinstance(texts, dict) and platform_key in texts:
                    post_text = texts[platform_key] or post_text
            except (json.JSONDecodeError, TypeError):
                pass

        images_raw = record.get("images")
        if isinstance(images_raw, str):
            images_decoded = images_raw
        else:
            images_decoded = json.dumps(images_raw, ensure_ascii=False) if images_raw else "[]"
        # Не перезаписывать images пустым значением: в tg_posts уже могли быть пути к файлам
        # (процессор мог очистить images через remove_images), иначе пост уйдёт без картинки
        has_images = bool(images_raw)
        if isinstance(images_raw, str):
            try:
                parsed = json.loads(images_raw)
                has_images = bool(parsed) if isinstance(parsed, list) else bool(parsed)
            except (json.JSONDecodeError, TypeError):
                has_images = bool(images_raw.strip() and images_raw.strip() != "[]")
        elif isinstance(images_raw, list):
            has_images = len(images_raw) > 0

        if has_images:
            await cur.execute(
                f"""
                UPDATE {target_table}
                SET status = 'ready',
                    post_text = %s,
                    images = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                """,
                (post_text, images_decoded, source_id, user_id),
            )
        else:
            await cur.execute(
                f"""
                UPDATE {target_table}
                SET status = 'ready',
                    post_text = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                """,
                (post_text, source_id, user_id),
            )
        logger.debug(
            "Updated %s id=%s (user_id=%s) to ready, images=%s",
            target_table,
            source_id,
            user_id,
            "set" if has_images else "preserved",
        )

    async def _insert_into_target(
        self,
        cur: Any,
        target_table: str,
        record: dict[str, Any],
    ) -> None:
        """Вставляет пост в целевую платформенную таблицу со статусом 'ready'."""
        insert_cols = list(_POST_COLUMNS)
        if target_table == "dzen_posts":
            insert_cols = list(_POST_COLUMNS) + ["videos"]
        elif target_table == "instagram_posts":
            insert_cols = list(_POST_COLUMNS) + ["videos"]
        placeholders = ", ".join(["%s"] * len(insert_cols))
        col_str = ", ".join(insert_cols)

        values = [record.get(c) for c in _POST_COLUMNS]

        # Статус в целевой таблице — 'ready' (для бота-публикатора)
        status_idx = _POST_COLUMNS.index("status")
        values[status_idx] = "ready"

        # В целевых таблицах images — JSONB; из posts приходит list/dict — приводим к JSON-строке
        images_idx = _POST_COLUMNS.index("images")
        if values[images_idx] is not None and not isinstance(values[images_idx], str):
            values[images_idx] = json.dumps(values[images_idx], ensure_ascii=False)

        if target_table == "dzen_posts":
            videos_val = record.get("videos")
            if videos_val is not None and not isinstance(videos_val, str):
                videos_val = json.dumps(videos_val, ensure_ascii=False)
            else:
                videos_val = "[]" if not videos_val else videos_val
            values.append(videos_val)
        elif target_table == "instagram_posts":
            videos_val = record.get("videos")
            if videos_val is not None and not isinstance(videos_val, str):
                videos_val = json.dumps(videos_val, ensure_ascii=False)
            else:
                videos_val = "[]" if not videos_val else videos_val
            values.append(videos_val)

        await cur.execute(
            f"""
            INSERT INTO {target_table} ({col_str})
            VALUES ({placeholders})
            """,
            values,
        )


distribute_service = DistributeService()
