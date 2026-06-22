"""Основной сервис обработки постов.

Оркестрирует весь pipeline:
1. Выбирает посты со статусом 'collected' из таблицы posts
2. Ставит статус 'processing'
3. Загружает настройки обработки из профиля пользователя
4. Применяет обработку текста (AI, эмодзи, картинки, HTML)
5. Подготавливает тексты для целевых платформ
6. Сохраняет результат со статусом 'ready' или 'review'
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection
from config import (
    settings,
    PROFILE_TABLE_MAP,
    PROCESSING_SETTINGS_FIELDS,
)
from services.text_cleaner import remove_emojis, remove_images, clean_html
from services.ai_processor import process_with_ai
from services.platform_formatter import prepare_platform_texts

logger = logging.getLogger(__name__)


class ProcessingService:
    """Сервис обработки постов из таблицы posts."""

    def __init__(self) -> None:
        self.last_run_at: Optional[datetime] = None
        self.total_processed: int = 0
        self.last_cycle_processed: int = 0

    async def run_processing_cycle(self) -> int:
        """Выполняет один цикл обработки.

        1. SELECT posts WHERE status = 'collected' FOR UPDATE SKIP LOCKED
        2. UPDATE status -> 'processing'
        3. Для каждого поста: загрузить настройки, обработать, сохранить

        Returns:
            Количество обработанных постов за цикл.
        """
        cycle_count = 0

        async with get_db_connection() as conn:
            cur = await conn.cursor()
            try:
                await cur.execute("BEGIN")

                # 1. Выбрать посты со статусом 'collected'
                await cur.execute(
                    """
                    SELECT id, user_id, source_platform, post_text, images,
                           to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram
                    FROM posts
                    WHERE status = 'collected'
                    ORDER BY created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (settings.PROCESS_BATCH_SIZE,),
                )
                rows = await cur.fetchall()

                if not rows:
                    await cur.execute("COMMIT")
                    self.last_run_at = datetime.utcnow()
                    self.last_cycle_processed = 0
                    return 0

                col_names = [
                    "id", "user_id", "source_platform", "post_text", "images",
                    "to_tg", "to_tw", "to_wp", "to_vk", "to_threads", "to_dzen", "to_instagram",
                ]

                # 2. Собрать ID и сразу выставить статус 'processing'
                post_ids = [row[0] for row in rows]
                ids_placeholder = ", ".join(["%s"] * len(post_ids))
                await cur.execute(
                    f"""
                    UPDATE posts
                    SET status = 'processing', updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({ids_placeholder})
                    """,
                    post_ids,
                )

                await cur.execute("COMMIT")

            except Exception:
                await cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

        # 3. Обработать каждый пост (вне транзакции блокировки)
        for row in rows:
            record = dict(zip(col_names, row))
            try:
                await self._process_single_post(record)
                cycle_count += 1
            except Exception:
                logger.exception("Error processing post id=%s", record["id"])
                # Откатить статус на 'collected' для повторной обработки
                await self._reset_post_status(record["id"], "collected")

        self.last_run_at = datetime.utcnow()
        self.last_cycle_processed = cycle_count
        self.total_processed += cycle_count

        if cycle_count > 0:
            logger.info("Processing cycle done: %d posts processed", cycle_count)

        return cycle_count

    async def _process_single_post(self, post: Dict[str, Any]) -> None:
        """Обрабатывает один пост полным pipeline.

        Args:
            post: Словарь с данными поста (id, user_id, source_platform, post_text, images, to_*).
        """
        post_id = post["id"]
        user_id = post["user_id"]
        source_platform = post.get("source_platform")
        text = post.get("post_text") or ""
        images = post.get("images") or []

        # Парсить images из JSON-строки, если нужно
        if isinstance(images, str):
            try:
                images = json.loads(images)
            except (json.JSONDecodeError, TypeError):
                images = []

        logger.debug("Processing post id=%s (user=%s, platform=%s)", post_id, user_id, source_platform)

        # Загрузить настройки обработки из профиля
        proc_settings = await self._load_processing_settings(user_id, source_platform)

        is_process_enabled = proc_settings.get("process_enabled", False)

        # Применить обработку текста (если process_enabled)
        if is_process_enabled:
            text, images = await self._apply_text_processing(text, images, proc_settings)

        # Подготовить тексты для целевых платформ (всегда)
        post_flags = {
            "to_tg": post.get("to_tg", False),
            "to_tw": post.get("to_tw", False),
            "to_wp": post.get("to_wp", False),
            "to_vk": post.get("to_vk", False),
            "to_threads": post.get("to_threads", False),
            "to_dzen": post.get("to_dzen", False),
            "to_instagram": post.get("to_instagram", False),
        }
        platform_texts = await prepare_platform_texts(
            text=text,
            post_flags=post_flags,
            is_add_static_html=proc_settings.get("add_static_html", False),
            static_html_content=proc_settings.get("static_html_content"),
        )

        # Определить финальный статус
        is_review = proc_settings.get("status_review_after_process", False)
        has_any_target = any(
            post.get(flag)
            for flag in ("to_tg", "to_tw", "to_wp", "to_vk", "to_threads", "to_dzen", "to_instagram")
        )
        if is_review or not has_any_target:
            final_status = "review"
            if not has_any_target:
                logger.debug(
                    "Post id=%s: no target platform (to_tg/to_wp/to_vk/to_tw/to_threads/to_dzen/to_instagram) -> status=review",
                    post_id,
                )
        else:
            final_status = "ready"

        # Сохранить результат
        await self._save_processed_post(
            post_id=post_id,
            text=text,
            images=images,
            platform_texts=platform_texts,
            status=final_status,
        )

        logger.info(
            "Post id=%s processed -> status=%s (platforms: %s)",
            post_id,
            final_status,
            ", ".join(platform_texts.keys()) if platform_texts else "none",
        )

    async def _load_processing_settings(
        self, user_id: int, source_platform: Optional[str]
    ) -> Dict[str, Any]:
        """Загружает настройки обработки из профиля пользователя.

        Маппинг source_platform -> таблица профиля:
        - tg -> tg_profiles (process_enabled)
        - wp -> wp_publish_profile (process_before_publish)
        - curl/url -> curl_settings (process_before_publish)

        Args:
            user_id: ID пользователя.
            source_platform: Платформа-источник поста.

        Returns:
            Словарь с настройками обработки. Пустой словарь, если профиль не найден.
        """
        if not source_platform or source_platform not in PROFILE_TABLE_MAP:
            logger.debug(
                "No profile mapping for source_platform=%s, skipping settings load",
                source_platform,
            )
            return {}

        mapping = PROFILE_TABLE_MAP[source_platform]
        table = mapping["table"]
        process_flag = mapping["process_flag"]
        description_field = mapping["process_description_field"]

        # Собрать список полей для SELECT
        fields = [process_flag, description_field] + PROCESSING_SETTINGS_FIELDS
        fields_str = ", ".join(fields)

        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"SELECT {fields_str} FROM {table} WHERE user_id = %s",
                        (user_id,),
                    )
                    row = await cur.fetchone()

                    if not row:
                        logger.debug(
                            "No profile found in %s for user_id=%s",
                            table,
                            user_id,
                        )
                        return {}

                    result: Dict[str, Any] = {}
                    for i, field in enumerate(fields):
                        value = row[i]
                        # Нормализовать имя поля process_enabled
                        if field == process_flag:
                            result["process_enabled"] = bool(value) if value is not None else False
                        elif field == description_field:
                            result["processing_description"] = value
                        else:
                            # Парсить JSONB-поля
                            if field == "process_services" and isinstance(value, str):
                                try:
                                    value = json.loads(value)
                                except (json.JSONDecodeError, TypeError):
                                    value = None
                            result[field] = value

                    return result

        except Exception:
            logger.exception(
                "Error loading processing settings from %s for user_id=%s",
                table,
                user_id,
            )
            return {}

    async def _apply_text_processing(
        self,
        text: str,
        images: List[str],
        proc_settings: Dict[str, Any],
    ) -> tuple[str, List[str]]:
        """Применяет обработку текста по настройкам.

        Порядок:
        1. AI-обработка по описанию (заглушка)
        2. Удаление эмодзи (если remove_emojis)
        3. Удаление картинок (если remove_images)
        4. Очистка HTML (если clean_html)

        Args:
            text: Исходный текст поста.
            images: Список URL изображений.
            proc_settings: Настройки обработки из профиля.

        Returns:
            Кортеж (обработанный текст, обновлённый список изображений).
        """
        # 1. AI-обработка (заглушка)
        description = proc_settings.get("processing_description")
        if description:
            text = await process_with_ai(text, description)

        # 2. Удаление эмодзи
        if proc_settings.get("remove_emojis", False):
            text = remove_emojis(text)
            logger.debug("Emojis removed from text")

        # 3. Удаление картинок
        if proc_settings.get("remove_images", False):
            text, images = remove_images(text, images)
            logger.debug("Images removed from post")

        # 4. Очистка HTML
        if proc_settings.get("clean_html", False):
            text = clean_html(text)
            logger.debug("HTML tags cleaned from text")

        return text, images

    async def _save_processed_post(
        self,
        post_id: int,
        text: str,
        images: List[str],
        platform_texts: Dict[str, str],
        status: str,
    ) -> None:
        """Сохраняет обработанный пост в БД.

        Args:
            post_id: ID поста.
            text: Обработанный текст (полный, без обрезки по платформам).
            images: Список изображений (может быть пустым после remove_images).
            platform_texts: Словарь {platform: text} для каждой целевой платформы.
            status: Финальный статус ('ready' или 'review').
        """
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE posts
                    SET post_text = %s,
                        images = %s,
                        platform_texts = %s,
                        status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        text,
                        json.dumps(images, ensure_ascii=False),
                        json.dumps(platform_texts, ensure_ascii=False),
                        status,
                        post_id,
                    ),
                )

    async def _reset_post_status(self, post_id: int, status: str) -> None:
        """Сбрасывает статус поста (при ошибке обработки).

        Args:
            post_id: ID поста.
            status: Статус для установки.
        """
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE posts
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (status, post_id),
                    )
        except Exception:
            logger.exception("Failed to reset post id=%s status to %s", post_id, status)


processing_service = ProcessingService()
