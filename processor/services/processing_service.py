"""Основной сервис обработки постов.

Оркестрирует pipeline:
1. Claim posts через PostsRepository
2. Настройки из профиля пользователя (*_profiles, не *_posts)
3. Обработка текста, platform_texts
4. post_targets (очередь публикации)
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection
from shared.db.posts_repo import (
    PostsRepository,
    flags_from_platforms,
    resolve_publish_platforms,
)
from shared.service_cycle_log import write_cycle_log
from config import (
    settings,
    PROFILE_TABLE_MAP,
    PROCESSING_SETTINGS_FIELDS,
)
from services.text_cleaner import apply_cpu_cleaning
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


class ProcessingService:
    """Сервис обработки постов из таблицы posts."""

    def __init__(self) -> None:
        self.last_run_at: Optional[datetime] = None
        self.total_processed: int = 0
        self.last_cycle_processed: int = 0
        self._profile_row_cache: dict[tuple[str, int], tuple[list[str], tuple[Any, ...]]] = {}

    async def run_processing_cycle(self) -> int:
        """Выполняет один цикл обработки.

        1. Claim posts (collected/created → processing) via PostsRepository
        2. For each post: load settings, process, save, write post_targets

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
                repo = PostsRepository(cur)
                records = await repo.claim_process(
                    limit=settings.PROCESS_BATCH_SIZE,
                    stale_minutes=int(getattr(settings, "STALE_PROCESSING_MINUTES", 15)),
                )
                await cur.execute("COMMIT")
            except Exception:
                await cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

        if not records:
            self.last_run_at = datetime.utcnow()
            self.last_cycle_processed = 0
            await _log_cycle(items_processed=0)
            return 0

        # 3. Обработать посты параллельно (CPU в threads; AI — семафор shared.ai_client)
        await self._prefetch_processing_settings(records)
        concurrency = max(1, int(getattr(settings, "PROCESS_CONCURRENCY", 8)))
        cycle_timeout = float(getattr(settings, "PROCESS_CYCLE_TIMEOUT_SEC", 90.0))
        deadline = time.monotonic() + cycle_timeout
        sem = asyncio.Semaphore(concurrency)
        done_ids: set[int] = set()

        async def _bounded(record: Dict[str, Any]) -> None:
            async with sem:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    await self._reset_post_status(record["id"], "collected")
                    return
                try:
                    await asyncio.wait_for(
                        self._process_single_post(record),
                        timeout=remaining,
                    )
                    done_ids.add(int(record["id"]))
                except TimeoutError:
                    logger.warning("Post id=%s exceeded cycle deadline; requeue", record["id"])
                    await self._reset_post_status(record["id"], "collected")
                except Exception:
                    logger.exception("Error processing post id=%s", record["id"])
                    await self._reset_post_status(record["id"], "collected")
                    done_ids.add(int(record["id"]))

        await asyncio.gather(*[_bounded(record) for record in records])
        cycle_count = len(done_ids)

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
        platforms = resolve_publish_platforms(
            legacy_flags=post,
            process_services=proc_settings.get("process_services"),
            source_platform=source_platform,
        )
        post_flags = flags_from_platforms(platforms)
        is_process_enabled = proc_settings.get("process_enabled", False)

        # Применить обработку текста (если process_enabled)
        if is_process_enabled:
            text, images = await self._apply_text_processing(text, images, proc_settings)

        if proc_settings.get("summarize_enabled") and len(text) > int(proc_settings.get("summarize_min_length") or 500):
            text = await summarize_text(text, settings.TELEGRAM_MAX_LENGTH)

        ai_enrichment = await self._maybe_enrich_text(text, proc_settings)

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
        has_any_target = bool(platforms)
        if is_review or not has_any_target:
            final_status = "review"
            if not has_any_target:
                logger.debug(
                    "Post id=%s: no publish targets -> status=review",
                    post_id,
                )
        else:
            final_status = "ready"

        # Сохранить результат
        await self._save_processed_post(
            post_id=post_id,
            user_id=int(user_id),
            text=text,
            images=images,
            platform_texts=platform_texts,
            status=final_status,
            platforms=platforms,
        )

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
        description = proc_settings.get("processing_description")
        if description:
            text = await process_with_ai(text, description)

        text, images = await asyncio.to_thread(apply_cpu_cleaning, text, images, proc_settings)
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
        """Return review posts with no destinations back to collected."""
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE posts p
                        SET status = 'collected', updated_at = CURRENT_TIMESTAMP
                        WHERE p.status = 'review'
                          AND NOT EXISTS (
                            SELECT 1
                            FROM post_targets t
                            WHERE t.post_id = p.id
                              AND t.status IN ('pending', 'ready', 'publishing')
                          )
                        """
                    )
                    return int(cur.rowcount or 0)
        except Exception:
            logger.exception("Failed to requeue orphan review posts")
            return 0

    async def _save_processed_post(
        self,
        post_id: int,
        user_id: int,
        text: str,
        images: List[str],
        platform_texts: Dict[str, str],
        status: str,
        platforms: List[str],
    ) -> None:
        """Save hub content and post_targets."""
        target_status = "ready" if status == "ready" else "pending"
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                repo = PostsRepository(cur)
                await repo.save_processed(
                    post_id=post_id,
                    text=text,
                    images=images,
                    platform_texts=platform_texts,
                    status=status,
                )
                if platforms:
                    await repo.ensure_targets(
                        post_id=post_id,
                        user_id=user_id,
                        platforms=platforms,
                        status=target_status,
                    )

    async def _reset_post_status(self, post_id: int, status: str) -> None:
        try:
            async with get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await PostsRepository(cur).set_posts_status([post_id], status)
        except Exception:
            logger.exception("Failed to reset post id=%s status to %s", post_id, status)


processing_service = ProcessingService()
