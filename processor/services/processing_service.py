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
from shared.service_cycle_log import write_cycle_log
from config import (
    settings,
    PROFILE_TABLE_MAP,
    PROCESSING_SETTINGS_FIELDS,
    PLATFORM_FLAGS,
)
from services.text_cleaner import remove_emojis, remove_images, clean_html
from services.ai_processor import process_with_ai, summarize_text
from services.platform_formatter import prepare_platform_texts

logger = logging.getLogger(__name__)


async def _log_cycle(
    *,
    status: str = "ok",
    detail: str | None = None,
    items_processed: int = 0,
) -> None:
    await write_cycle_log(
        get_db_connection,
        service_name="processor",
        cycle_type="process",
        status=status,
        detail=detail,
        items_processed=items_processed,
    )

def _match_url_config(urls: List[Any], post_url: Optional[str]) -> Optional[Dict[str, Any]]:
    """Находит curl urls[] item по URL поста."""
    if not post_url or not isinstance(urls, list):
        return None
    needle = str(post_url).strip()
    if not needle:
        return None
    candidates = [u for u in urls if isinstance(u, dict)]
    for u in candidates:
        if str(u.get("url") or "").strip() == needle:
            return u
    needle_norm = needle.rstrip("/")
    for u in candidates:
        if str(u.get("url") or "").strip().rstrip("/") == needle_norm:
            return u
    return None


_SERVICE_NAME_TO_FLAG = {name: flag for flag, name in PLATFORM_FLAGS.items()}
_DESTINATION_FLAGS = list(PLATFORM_FLAGS.keys())
_SOURCE_PLATFORM_TABLE = {
    "tg": "tg_posts",
    "wp": "wp_posts",
    "url": "url_posts",
    "curl": "url_posts",
    "vk": "vk_posts",
    "tw": "tw_posts",
    "threads": "threads_posts",
    "instagram": "instagram_posts",
    "dzen": "dzen_posts",
    "cpost": "cpost_posts",
}


class ProcessingService:
    """Сервис обработки постов из таблицы posts."""

    def __init__(self) -> None:
        self.last_run_at: Optional[datetime] = None
        self.total_processed: int = 0
        self.last_cycle_processed: int = 0
        self._profile_row_cache: dict[tuple[str, int], tuple[list[str], tuple[Any, ...]]] = {}

    async def run_processing_cycle(self) -> int:
        """Выполняет один цикл обработки.

        1. SELECT posts WHERE status = 'collected' FOR UPDATE SKIP LOCKED
        2. UPDATE status -> 'processing'
        3. Для каждого поста: загрузить настройки, обработать, сохранить

        Returns:
            Количество обработанных постов за цикл.
        """
        cycle_count = 0

        requeued = await self._requeue_orphan_reviews()
        if requeued:
            logger.info("Requeued %d orphan review posts without destination flags", requeued)

        async with get_db_connection() as conn:
            cur = await conn.cursor()
            try:
                await cur.execute("BEGIN")

                # 1. Выбрать посты со статусом 'collected'
                await cur.execute(
                    """
                    SELECT id, user_id, source_platform, source_id, post_text, images, url,
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
                    await _log_cycle(items_processed=0)
                    return 0

                col_names = [
                    "id", "user_id", "source_platform", "source_id", "post_text", "images", "url",
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
        records = [dict(zip(col_names, row)) for row in rows]
        await self._prefetch_processing_settings(records)
        for record in records:
            try:
                await self._process_single_post(record)
                cycle_count += 1
            except Exception:
                logger.exception("Error processing post id=%s", record["id"])
                await self._reset_post_status(record["id"], "collected")

        self.last_run_at = datetime.utcnow()
        self.last_cycle_processed = cycle_count
        self.total_processed += cycle_count

        if cycle_count > 0:
            logger.info("Processing cycle done: %d posts processed", cycle_count)

        await _log_cycle(items_processed=cycle_count)
        self._profile_row_cache.clear()
        return cycle_count

    def _fields_for_platform(self, source_platform: str) -> tuple[Any, ...] | None:
        if source_platform not in PROFILE_TABLE_MAP:
            return None
        mapping = PROFILE_TABLE_MAP[source_platform]
        fields = [mapping["process_flag"], mapping["process_description_field"]] + PROCESSING_SETTINGS_FIELDS
        if source_platform in ("url", "curl"):
            fields = ["urls"] + fields
        if source_platform == "tg":
            fields.extend([
                "summarize_enabled",
                "summarize_min_length",
                "classification_enabled",
                "classification_categories",
            ])
        return mapping, fields

    def _row_to_processing_settings(
        self,
        source_platform: str,
        fields: list[str],
        row_values: tuple[Any, ...],
        post_url: Optional[str],
    ) -> Dict[str, Any]:
        mapping = PROFILE_TABLE_MAP[source_platform]
        process_flag = mapping["process_flag"]
        description_field = mapping["process_description_field"]
        result: Dict[str, Any] = {}
        url_item: Optional[Dict[str, Any]] = None
        for i, field in enumerate(fields):
            value = row_values[i]
            if field == "urls":
                if isinstance(value, str):
                    try:
                        value = json.loads(value) if value else []
                    except (json.JSONDecodeError, TypeError):
                        value = []
                url_item = _match_url_config(value if isinstance(value, list) else [], post_url)
                continue
            if field == process_flag:
                result["process_enabled"] = bool(value) if value is not None else False
            elif field == description_field:
                result["processing_description"] = value
            else:
                if field == "process_services" and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        value = None
                if field == "classification_categories" and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        value = []
                result[field] = value

        if url_item is not None:
            if "process_before_publish" in url_item:
                result["process_enabled"] = bool(url_item.get("process_before_publish"))
            if "process_description" in url_item:
                result["processing_description"] = url_item.get("process_description")
            for key in PROCESSING_SETTINGS_FIELDS:
                if key in url_item:
                    value = url_item.get(key)
                    if key == "process_services" and isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            value = None
                    result[key] = value
        return result

    async def _prefetch_processing_settings(self, posts: List[Dict[str, Any]]) -> None:
        """Batch-load profile rows for all posts in the current cycle."""
        self._profile_row_cache.clear()
        by_platform: dict[str, set[int]] = {}
        for post in posts:
            platform = post.get("source_platform")
            user_id = post.get("user_id")
            if not platform or user_id is None or platform not in PROFILE_TABLE_MAP:
                continue
            by_platform.setdefault(platform, set()).add(int(user_id))

        for platform, user_ids in by_platform.items():
            mapping_fields = self._fields_for_platform(platform)
            if mapping_fields is None:
                continue
            mapping, fields = mapping_fields
            table = mapping["table"]
            fields_str = ", ".join(fields)
            ids = list(user_ids)
            placeholders = ", ".join(["%s"] * len(ids))
            try:
                async with get_db_connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            f"SELECT user_id, {fields_str} FROM {table} WHERE user_id IN ({placeholders})",
                            ids,
                        )
                        for row in await cur.fetchall():
                            self._profile_row_cache[(platform, int(row[0]))] = (fields, tuple(row[1:]))
            except Exception:
                logger.exception("Failed to prefetch profiles from %s", table)

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

        # Загрузить настройки обработки из профиля (для url/curl — per-URL)
        proc_settings = await self._load_processing_settings(
            user_id,
            source_platform,
            post_url=post.get("url"),
        )
        self._apply_destination_flags(post, proc_settings)

        is_process_enabled = proc_settings.get("process_enabled", False)

        # Применить обработку текста (если process_enabled)
        if is_process_enabled:
            text, images = await self._apply_text_processing(text, images, proc_settings)

        if proc_settings.get("summarize_enabled") and len(text) > int(proc_settings.get("summarize_min_length") or 500):
            text = await summarize_text(text, settings.TELEGRAM_MAX_LENGTH)

        ai_enrichment = await self._maybe_enrich_text(text, proc_settings)

        # Подготовить тексты для целевых платформ (всегда)
        post_flags = {flag: bool(post.get(flag)) for flag in _DESTINATION_FLAGS}
        platform_texts = await prepare_platform_texts(
            text=text,
            post_flags=post_flags,
            is_add_static_html=proc_settings.get("add_static_html", False),
            static_html_content=proc_settings.get("static_html_content"),
        )
        if ai_enrichment:
            platform_texts["_ai_enrichment"] = json.dumps(ai_enrichment, ensure_ascii=False)

        # Определить финальный статус
        is_review = proc_settings.get("status_review_after_process", False)
        has_any_target = any(post_flags.values())
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
            destination_flags=post_flags,
        )
        await self._sync_source_status(post, final_status)

        logger.info(
            "Post id=%s processed -> status=%s (platforms: %s)",
            post_id,
            final_status,
            ", ".join(k for k in platform_texts.keys() if not k.startswith("_")) or "none",
        )

    async def _load_processing_settings(
        self,
        user_id: int,
        source_platform: Optional[str],
        post_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Загружает настройки обработки из профиля пользователя.

        Маппинг source_platform -> таблица профиля:
        - tg -> tg_profiles (process_enabled)
        - wp -> wp_publish_profile (process_before_publish)
        - curl/url -> curl_settings (per-URL processing из urls[], fallback на global)

        Args:
            user_id: ID пользователя.
            source_platform: Платформа-источник поста.
            post_url: URL поста (для match в curl_settings.urls).

        Returns:
            Словарь с настройками обработки. Пустой словарь, если профиль не найден.
        """
        if not source_platform or source_platform not in PROFILE_TABLE_MAP:
            logger.debug(
                "No profile mapping for source_platform=%s, skipping settings load",
                source_platform,
            )
            return {}

        cached = self._profile_row_cache.get((source_platform, user_id))
        if cached is not None:
            fields, row_values = cached
            return self._row_to_processing_settings(source_platform, fields, row_values, post_url)

        mapping_fields = self._fields_for_platform(source_platform)
        if mapping_fields is None:
            return {}
        mapping, fields = mapping_fields
        table = mapping["table"]
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

                    return self._row_to_processing_settings(
                        source_platform,
                        fields,
                        tuple(row),
                        post_url,
                    )

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

    async def _maybe_enrich_text(
        self,
        text: str,
        proc_settings: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not proc_settings.get("classification_enabled") or not text:
            return None
        try:
            import sys
            from pathlib import Path

            root = Path(__file__).resolve().parent.parent.parent
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from shared import ai_client

            if not await ai_client.is_ready():
                logger.debug("AI enrichment skipped: AI not ready")
                return None

            categories = proc_settings.get("classification_categories") or []
            if isinstance(categories, str):
                categories = json.loads(categories)
            return await ai_client.enrich(text, categories)
        except Exception:
            logger.exception("AI enrichment failed")
            return None

    async def _requeue_orphan_reviews(self) -> int:
        """Возвращает в collected review-посты без to_* — иначе они навсегда зависают."""
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE posts
                        SET status = 'collected', updated_at = CURRENT_TIMESTAMP
                        WHERE status = 'review'
                          AND COALESCE(to_tg, false) = false
                          AND COALESCE(to_tw, false) = false
                          AND COALESCE(to_wp, false) = false
                          AND COALESCE(to_vk, false) = false
                          AND COALESCE(to_threads, false) = false
                          AND COALESCE(to_dzen, false) = false
                          AND COALESCE(to_instagram, false) = false
                        """
                    )
                    return int(cur.rowcount or 0)
        except Exception:
            logger.exception("Failed to requeue orphan review posts")
            return 0

    def _apply_destination_flags(
        self,
        post: Dict[str, Any],
        proc_settings: Dict[str, Any],
    ) -> None:
        """Заполняет to_* из process_services, если флаги ещё не заданы."""
        if any(post.get(flag) for flag in _DESTINATION_FLAGS):
            return

        services = proc_settings.get("process_services") or []
        if isinstance(services, str):
            try:
                services = json.loads(services)
            except (json.JSONDecodeError, TypeError):
                services = []
        if not isinstance(services, list):
            services = []

        for item in services:
            flag = _SERVICE_NAME_TO_FLAG.get(str(item).strip().lower())
            if flag:
                post[flag] = True

        if any(post.get(flag) for flag in _DESTINATION_FLAGS):
            return

        # Сбор из TG без выбранных сервисов: публикуем обратно в Telegram
        if post.get("source_platform") == "tg":
            post["to_tg"] = True

    async def _sync_source_status(self, post: Dict[str, Any], status: str) -> None:
        """Синхронизирует статус исходной *_posts записи (processing → ready/review)."""
        source_platform = post.get("source_platform")
        source_id = post.get("source_id")
        table = _SOURCE_PLATFORM_TABLE.get(source_platform or "")
        if not table or source_id is None:
            return
        # Distribute сам переводит source в ready при status=ready + to_*
        if status == "ready":
            return
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"""
                        UPDATE {table}
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (status, source_id),
                    )
        except Exception:
            logger.exception(
                "Failed to sync source status table=%s id=%s status=%s",
                table,
                source_id,
                status,
            )

    async def _save_processed_post(
        self,
        post_id: int,
        text: str,
        images: List[str],
        platform_texts: Dict[str, str],
        status: str,
        destination_flags: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Сохраняет обработанный пост в БД.

        Args:
            post_id: ID поста.
            text: Обработанный текст (полный, без обрезки по платформам).
            images: Список изображений (может быть пустым после remove_images).
            platform_texts: Словарь {platform: text} для каждой целевой платформы.
            status: Финальный статус ('ready' или 'review').
            destination_flags: Флаги to_* для записи в posts.
        """
        flags = destination_flags or {}
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE posts
                    SET post_text = %s,
                        images = %s,
                        platform_texts = %s,
                        status = %s,
                        to_tg = %s,
                        to_tw = %s,
                        to_wp = %s,
                        to_vk = %s,
                        to_threads = %s,
                        to_dzen = %s,
                        to_instagram = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        text,
                        json.dumps(images, ensure_ascii=False),
                        json.dumps(platform_texts, ensure_ascii=False),
                        status,
                        bool(flags.get("to_tg")),
                        bool(flags.get("to_tw")),
                        bool(flags.get("to_wp")),
                        bool(flags.get("to_vk")),
                        bool(flags.get("to_threads")),
                        bool(flags.get("to_dzen")),
                        bool(flags.get("to_instagram")),
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
