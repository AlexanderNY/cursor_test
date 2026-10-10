"""Hourly channel digests: hold → AI summary → posts/post_targets."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.digest import (
    DEFAULT_SUMMARY_PROMPT,
    clamp_interval_min,
    combine_digest_texts,
    cover_image_from_pack,
    is_digest_due,
    parse_channel_ids,
    parse_digest_ai_payload,
    pick_cover_pack,
    should_create_digest,
    should_notify_cover_miss,
)
from shared.post_adapt import normalize_network

logger = logging.getLogger(__name__)

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore

try:
    from shared.ai_quota import AiQuotaExceeded, consume_ai_calls
except ImportError:
    AiQuotaExceeded = Exception  # type: ignore
    consume_ai_calls = None  # type: ignore

_digest_stats: Dict[str, Any] = {
    "sent": 0,
    "skipped_empty": 0,
    "skipped_quota": 0,
    "cover_attached": 0,
    "cover_miss": 0,
    "errors": 0,
    "last_latency_ms": None,
}


def get_digest_stats() -> Dict[str, Any]:
    return dict(_digest_stats)


class SummaryAggregator:
    """Periodically turns digest_hold posts into one publishable summary."""

    def __init__(self) -> None:
        self._notification_service = None
        try:
            from services.notification_service import NotificationService

            self._notification_service = NotificationService()
        except Exception:
            self._notification_service = None

    async def run_digest_cycle(self, client_manager=None) -> int:
        del client_manager  # publication goes through post_targets / bots
        if not ai_client:
            return 0

        jobs = await self._load_due_jobs()
        digests_sent = 0
        for job in jobs:
            try:
                created = await self._run_one_job(job)
                if created:
                    digests_sent += 1
                    _digest_stats["sent"] = int(_digest_stats["sent"]) + 1
            except Exception as exc:
                _digest_stats["errors"] = int(_digest_stats["errors"]) + 1
                logger.error(
                    "Digest job id=%s failed: %s",
                    job.get("id"),
                    exc,
                    exc_info=True,
                )
        return digests_sent

    async def _load_due_jobs(self) -> List[Dict[str, Any]]:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT j.id, j.brand_id, j.user_id, j.enabled, j.source_channel_ids,
                               j.publish_channel_id, j.interval_min, j.process_prompt,
                               j.summary_prompt, j.attach_cover_image,
                               j.last_cover_miss_theme, j.last_cover_miss_at, j.last_run_at,
                               c.network AS publish_network,
                               c.external_id AS publish_external_id,
                               c.role AS publish_role,
                               c.publish_enabled AS publish_enabled
                        FROM smm_digest_jobs j
                        LEFT JOIN smm_brand_channels c ON c.id = j.publish_channel_id
                        WHERE j.enabled = TRUE
                          AND j.publish_channel_id IS NOT NULL
                        """
                    )
                    rows = await cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    jobs = [dict(zip(cols, row)) for row in rows]
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to load digest jobs: %s", exc)
            return []

        due: List[Dict[str, Any]] = []
        now = datetime.utcnow()
        for job in jobs:
            interval = clamp_interval_min(job.get("interval_min"))
            if not is_digest_due(job.get("last_run_at"), interval, now=now):
                continue
            sources = parse_channel_ids(job.get("source_channel_ids"))
            if not sources:
                continue
            network = normalize_network(job.get("publish_network") or "")
            external_id = str(job.get("publish_external_id") or "").strip()
            if network not in ("tg", "vk") or not external_id:
                logger.warning(
                    "Digest job id=%s skipped: publish channel missing/unsupported",
                    job.get("id"),
                )
                continue
            job["source_channel_ids"] = sources
            job["interval_min"] = interval
            job["publish_network"] = network
            job["publish_external_id"] = external_id
            job["attach_cover_image"] = bool(job.get("attach_cover_image", True))
            due.append(job)
        return due

    async def _run_one_job(self, job: Dict[str, Any]) -> bool:
        job_id = int(job["id"])
        user_id = int(job["user_id"])
        brand_id = int(job["brand_id"])
        source_ids = list(job["source_channel_ids"])
        network = job["publish_network"]
        external_id = job["publish_external_id"]
        attach_cover = bool(job.get("attach_cover_image", True))
        cover_miss = False
        notify_now = False
        theme = ""
        tags: List[str] = []

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                await cur.execute(
                    "SELECT pg_try_advisory_xact_lock(%s)",
                    (1000000 + job_id,),
                )
                locked_row = await cur.fetchone()
                if not locked_row or not locked_row[0]:
                    await cur.execute("ROLLBACK")
                    return False

                placeholders = ", ".join(["%s"] * len(source_ids))
                await cur.execute(
                    f"""
                    SELECT id, user_id, brand_id, channel_id, domain, post_text
                    FROM posts
                    WHERE status = 'digest_hold'
                      AND channel_id IN ({placeholders})
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    """,
                    source_ids,
                )
                rows = await cur.fetchall()
                cols = [d[0] for d in cur.description]
                posts = [dict(zip(cols, row)) for row in rows]

                if not should_create_digest(posts):
                    await cur.execute(
                        """
                        UPDATE smm_digest_jobs
                        SET last_run_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (job_id,),
                    )
                    await cur.execute("COMMIT")
                    _digest_stats["skipped_empty"] = int(_digest_stats["skipped_empty"]) + 1
                    return False

                payload = await self._build_digest_payload(
                    posts,
                    user_id=user_id,
                    summary_prompt=job.get("summary_prompt"),
                )
                if not payload or not payload.get("summary"):
                    await cur.execute("ROLLBACK")
                    return False

                digest_text = str(payload["summary"]).strip()
                theme = str(payload.get("theme") or "").strip()
                tags = list(payload.get("tags") or [])
                images: List[str] = []
                if attach_cover:
                    await cur.execute(
                        """
                        SELECT id, title, object_keys, tags
                        FROM smm_media_packs
                        WHERE brand_id = %s
                        ORDER BY updated_at DESC NULLS LAST, id DESC
                        """,
                        (brand_id,),
                    )
                    pack_rows = await cur.fetchall()
                    pack_cols = [d[0] for d in cur.description]
                    packs = [dict(zip(pack_cols, row)) for row in pack_rows]
                    matched = pick_cover_pack(packs, tags or ([theme] if theme else []))
                    cover = cover_image_from_pack(matched)
                    if cover:
                        images = [cover]
                        _digest_stats["cover_attached"] = (
                            int(_digest_stats["cover_attached"]) + 1
                        )
                    else:
                        cover_miss = True
                        _digest_stats["cover_miss"] = int(_digest_stats["cover_miss"]) + 1

                repo = PostsRepository(cur)
                target_channels = [external_id] if network == "tg" else []
                target_groups = [external_id] if network == "vk" else []
                native_id = f"digest:{job_id}:{int(time.time())}"
                created = await repo.create_inbound(
                    InboundPostCreate(
                        user_id=user_id,
                        brand_id=brand_id,
                        channel_id=int(job["publish_channel_id"]),
                        source_platform=network,
                        source_native_id=native_id,
                        domain=external_id,
                        post_text=digest_text,
                        title="Сводка",
                        images=images,
                        extras={
                            "metadata": {
                                "digest_job_id": job_id,
                                "source_post_ids": [int(p["id"]) for p in posts],
                                "message_count": len(posts),
                                "theme": theme,
                                "theme_tags": tags,
                                "cover_attached": bool(images),
                            }
                        },
                        target_channels=target_channels,
                        target_groups=target_groups,
                        target_platforms=(network,),
                        target_status="ready",
                        status="ready",
                    )
                )

                source_ids_posts = [int(p["id"]) for p in posts]
                await repo.set_posts_status(source_ids_posts, "digested")

                if cover_miss:
                    notify_now = should_notify_cover_miss(
                        theme=theme or ",".join(tags) or "unknown",
                        last_theme=job.get("last_cover_miss_theme"),
                        last_at=job.get("last_cover_miss_at"),
                    )
                    if notify_now:
                        await cur.execute(
                            """
                            UPDATE smm_digest_jobs
                            SET last_run_at = CURRENT_TIMESTAMP,
                                last_cover_miss_theme = %s,
                                last_cover_miss_at = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (theme or ",".join(tags) or "unknown", job_id),
                        )
                    else:
                        await cur.execute(
                            """
                            UPDATE smm_digest_jobs
                            SET last_run_at = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (job_id,),
                        )
                else:
                    await cur.execute(
                        """
                        UPDATE smm_digest_jobs
                        SET last_run_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (job_id,),
                    )

                chat_id = 0
                try:
                    chat_id = int(external_id)
                except (TypeError, ValueError):
                    chat_id = 0
                await cur.execute(
                    """
                    INSERT INTO tg_digests (user_id, chat_id, digest_text, message_count)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, chat_id, digest_text, len(posts)),
                )
                await cur.execute("COMMIT")
                logger.info(
                    "Digest job id=%s created post id=%s from %d held messages cover=%s",
                    job_id,
                    created.get("id"),
                    len(posts),
                    bool(images),
                )
        except Exception:
            try:
                async with conn.cursor() as cur:
                    await cur.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            await release_db_connection(conn)

        if cover_miss and notify_now:
            await self._notify_cover_miss(
                user_id=user_id,
                theme=theme or ",".join(tags) or "unknown",
                tags=tags,
            )
        return True

    async def _notify_cover_miss(
        self,
        *,
        user_id: int,
        theme: str,
        tags: List[str],
    ) -> None:
        if not self._notification_service:
            return
        tag_part = ", ".join(tags[:8]) if tags else theme
        message = (
            f"Часовая сводка: нет media pack для темы «{theme}» "
            f"(теги: {tag_part}). "
            f'<a href="/library" style="color:#60a5fa;text-decoration:underline">'
            f"Загрузите заготовку с этими тегами в Library</a>."
        )
        try:
            await self._notification_service.send_notification(
                user_id,
                message,
                notif_type="digest_cover_missing",
            )
        except Exception as exc:
            logger.warning("Cover-miss notification failed user=%s: %s", user_id, exc)

    async def _build_digest_payload(
        self,
        posts: List[Dict[str, Any]],
        *,
        user_id: int,
        summary_prompt: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if consume_ai_calls is not None:
            try:
                await consume_ai_calls(
                    int(user_id),
                    units=1,
                    acquire=get_db_connection,
                    release=release_db_connection,
                )
            except AiQuotaExceeded:
                _digest_stats["skipped_quota"] = int(_digest_stats["skipped_quota"]) + 1
                logger.info("Digest skipped: AI quota exceeded user=%s", user_id)
                return None
            except Exception as exc:
                logger.warning("AI quota check failed for digest, continuing: %s", exc)

        combined = combine_digest_texts(posts)
        if not combined:
            return None
        base_system = (summary_prompt or "").strip() or DEFAULT_SUMMARY_PROMPT
        system = (
            f"{base_system}\n\n"
            "Ответь строго JSON без markdown: "
            '{"summary":"...","theme":"краткая тема","tags":["тег1","тег2"]}. '
            "tags — 2–6 коротких ключевых слов на русском для подбора картинки."
        )
        prompt = f"Сделай сводку из {len(posts)} сообщений.\n\n{combined}"
        try:
            started = time.perf_counter()
            result = await ai_client.complete(
                prompt, system=system, max_tokens=1024
            )
            _digest_stats["last_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 1
            )
            return parse_digest_ai_payload(result or "")
        except Exception as exc:
            _digest_stats["errors"] = int(_digest_stats["errors"]) + 1
            logger.warning("Digest generation failed: %s", exc)
            return None
