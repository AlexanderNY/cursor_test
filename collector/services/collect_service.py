"""Фаза 1: Сбор постов из платформенных таблиц (*_posts) в центральную таблицу posts."""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from database import get_db_connection
from config import settings, SOURCE_TABLES
from shared.db.post_columns import POST_BASE_COLUMNS
from shared.service_cycle_log import write_cycle_log

logger = logging.getLogger(__name__)

_POST_COLUMNS = list(POST_BASE_COLUMNS)


class CollectService:
    """Сервис сбора постов из *_posts -> posts."""

    def __init__(self) -> None:
        self.last_run_at: datetime | None = None
        self.total_collected: int = 0
        self.last_cycle_collected: int = 0

    async def run_collect_cycle(self) -> tuple[int, list[str]]:
        """Выполняет один цикл сбора.

        Для каждой таблицы из SOURCE_TABLES:
        1. SELECT ... WHERE status IN ('collected', 'created') FOR UPDATE SKIP LOCKED
        2. INSERT INTO posts с source_platform / source_id
        3. UPDATE source status -> 'processing'

        Returns:
            (Количество собранных постов за цикл, список ошибок по таблицам).
        """
        cycle_count = 0
        errors: list[str] = []

        for source in SOURCE_TABLES:
            platform = source["platform"]
            table = source["table"]
            try:
                count = await self._collect_from_table(platform, table)
                cycle_count += count
                if count > 0:
                    logger.info(
                        "Collected %d posts from %s", count, table
                    )
            except Exception as e:
                err_msg = f"{table}: {e!s}"
                errors.append(err_msg)
                logger.exception("Error collecting from %s: %s", table, e)

        self.last_run_at = datetime.utcnow()
        self.last_cycle_collected = cycle_count
        self.total_collected += cycle_count

        if cycle_count > 0:
            logger.info("Collect cycle done: %d posts total", cycle_count)
        if errors:
            logger.warning("Collect cycle had %d error(s): %s", len(errors), errors)

        await write_cycle_log(
            get_db_connection,
            service_name="collector",
            cycle_type="collect",
            status="error" if errors and cycle_count == 0 else ("partial" if errors else "ok"),
            detail="; ".join(errors) if errors else None,
            items_processed=cycle_count,
        )

        return cycle_count, errors

    async def _collect_from_table(self, platform: str, table: str) -> int:
        """Собирает посты из одной платформенной таблицы.

        Работает внутри одной транзакции для атомарности.
        """
        batch_size = settings.COLLECT_BATCH_SIZE
        actually_collected_ids: list[int] = []

        async with get_db_connection() as conn:
            cur = await conn.cursor()
            try:
                await cur.execute("BEGIN")

                # Таблицы с колонкой videos (для копирования в posts)
                tables_with_videos = ("dzen_posts", "instagram_posts")
                select_cols = list(_POST_COLUMNS) + (["videos"] if table in tables_with_videos else [])

                # 1. Выбрать посты со статусом 'collected' или 'created' (ожидают переноса в posts)
                await cur.execute(
                    f"""
                    SELECT id, {", ".join(select_cols)}
                    FROM {table}
                    WHERE status IN ('collected', 'created')
                    ORDER BY created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (batch_size,),
                )
                rows = await cur.fetchall()

                if not rows:
                    await cur.execute("COMMIT")
                    return 0

                # Получаем описание колонок
                col_names = ["id"] + list(select_cols)

                for row in rows:
                    record = dict(zip(col_names, row))
                    source_id = record["id"]

                    # Backfill brand/channel from smm_brand_channels when bots didn't set them
                    if record.get("brand_id") is None or record.get("channel_id") is None:
                        brand_id, channel_id = await self._resolve_brand_channel(
                            cur,
                            user_id=int(record["user_id"]),
                            platform=platform,
                            domain=record.get("domain"),
                            target_channels=record.get("target_channels"),
                            target_groups=record.get("target_groups"),
                        )
                        if record.get("brand_id") is None:
                            record["brand_id"] = brand_id
                        if record.get("channel_id") is None:
                            record["channel_id"] = channel_id

                    # 2. Вставить в posts с source_platform / source_id
                    insert_cols = list(_POST_COLUMNS) + [
                        "source_platform",
                        "source_id",
                    ]
                    if table in tables_with_videos:
                        insert_cols = list(_POST_COLUMNS) + ["videos", "source_platform", "source_id"]
                    placeholders = ", ".join(["%s"] * len(insert_cols))
                    col_str = ", ".join(insert_cols)

                    # Подготовка значений
                    values = [record[c] for c in _POST_COLUMNS]
                    if table in tables_with_videos:
                        videos_val = record.get("videos")
                        if videos_val is not None and not isinstance(videos_val, str):
                            videos_val = json.dumps(videos_val, ensure_ascii=False)
                        values = values + [videos_val or "[]"]
                    values.append(platform)  # source_platform
                    values.append(source_id)  # source_id

                    # Статус в posts — 'collected' (далее processor переведёт в 'processing')
                    status_idx = _POST_COLUMNS.index("status")
                    values[status_idx] = "collected"

                    # В posts.images тип JSONB; в tg_posts/url_posts может быть jsonb или text[] — приводим к JSON-строке
                    images_idx = _POST_COLUMNS.index("images")
                    if values[images_idx] is not None and not isinstance(values[images_idx], str):
                        values[images_idx] = json.dumps(values[images_idx], ensure_ascii=False)

                    for json_col in ("target_channels", "target_groups"):
                        idx = _POST_COLUMNS.index(json_col)
                        if values[idx] is None:
                            values[idx] = "[]"
                        elif not isinstance(values[idx], str):
                            values[idx] = json.dumps(values[idx], ensure_ascii=False)

                    await cur.execute(
                        f"""
                        INSERT INTO posts ({col_str})
                        VALUES ({placeholders})
                        ON CONFLICT (source_platform, source_id)
                            WHERE source_platform IS NOT NULL
                        DO NOTHING
                        RETURNING id
                        """,
                        values,
                    )
                    inserted = await cur.fetchone()
                    if inserted:
                        actually_collected_ids.append(source_id)
                        # Persist tenancy back onto the source row when we resolved it
                        if record.get("brand_id") is not None or record.get("channel_id") is not None:
                            await cur.execute(
                                f"""
                                UPDATE {table}
                                SET brand_id = COALESCE(brand_id, %s),
                                    channel_id = COALESCE(channel_id, %s),
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                                """,
                                (record.get("brand_id"), record.get("channel_id"), source_id),
                            )

                if actually_collected_ids:
                    ids_placeholder = ", ".join(["%s"] * len(actually_collected_ids))
                    await cur.execute(
                        f"""
                        UPDATE {table}
                        SET status = 'processing', updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({ids_placeholder})
                        """,
                        actually_collected_ids,
                    )

                await cur.execute("COMMIT")
                return len(actually_collected_ids)

            except Exception:
                await cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

    @staticmethod
    async def _resolve_brand_channel(
        cur,
        *,
        user_id: int,
        platform: str,
        domain: Any,
        target_channels: Any,
        target_groups: Any,
    ) -> tuple[Optional[int], Optional[int]]:
        """Map post domain/targets to smm_brand_channels for the user."""
        candidates: list[str] = []
        for raw in (domain,):
            if raw is None:
                continue
            s = str(raw).strip()
            if s:
                candidates.append(s)
        for blob in (target_channels, target_groups):
            if blob is None:
                continue
            if isinstance(blob, str):
                try:
                    blob = json.loads(blob)
                except (json.JSONDecodeError, TypeError):
                    blob = [blob]
            if isinstance(blob, list):
                for item in blob:
                    s = str(item).strip()
                    if s:
                        candidates.append(s)
        if not candidates:
            return None, None

        # Normalize network aliases
        network = platform
        if network == "twitter":
            network = "tw"
        if network == "wordpress":
            network = "wp"

        await cur.execute(
            """
            SELECT c.id, c.brand_id, c.external_id
            FROM smm_brand_channels c
            JOIN smm_brands b ON b.id = c.brand_id
            WHERE b.user_id = %s AND c.network = %s
            """,
            (user_id, network),
        )
        rows = await cur.fetchall()
        if not rows:
            return None, None

        cand_set = set(candidates)
        for stripped in list(candidates):
            cand_set.add(stripped.lstrip("-"))
            try:
                n = int(stripped)
                cand_set.update({str(n), str(abs(n)), str(-abs(n))})
            except ValueError:
                pass

        for ch_id, brand_id, external_id in rows:
            ext = str(external_id or "").strip()
            if not ext:
                continue
            variants = {ext, ext.lstrip("-")}
            try:
                n = int(ext)
                variants.update({str(n), str(abs(n)), str(-abs(n))})
            except ValueError:
                pass
            if variants & cand_set:
                return int(brand_id) if brand_id is not None else None, int(ch_id)

        return None, None


collect_service = CollectService()
