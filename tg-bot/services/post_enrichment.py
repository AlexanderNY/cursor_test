"""AI-enrichment собранных tg_posts (category, sentiment)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

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

# Rolling metrics for /health
_enrich_stats: Dict[str, Any] = {
    "enriched": 0,
    "skipped_quota": 0,
    "errors": 0,
    "last_latency_ms": None,
    "avg_latency_ms": None,
}
_latency_samples: List[float] = []


def get_enrichment_stats() -> Dict[str, Any]:
    return dict(_enrich_stats)


class PostEnrichmentService:
    """Обогащает tg_posts метаданными через AI."""

    async def enrich_post_if_enabled(
        self,
        post_id: int,
        text: str,
        profile: Dict[str, Any],
        *,
        user_id: Optional[int] = None,
        force: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if not ai_client:
            return None

        classification_enabled = profile.get("classification_enabled", False)
        batch_mode = profile.get("batch_enrichment_enabled", False)
        if not force and batch_mode:
            return None
        if not classification_enabled or not text:
            return None

        categories = self._parse_categories(profile.get("classification_categories"))
        uid = user_id if user_id is not None else profile.get("user_id")
        return await self._enrich_and_persist(post_id, text, categories, uid)

    async def run_batch_cycle(self, limit: int = 20) -> int:
        """Offline classify+sentiment for profiles with batch_enrichment_enabled."""
        if not ai_client:
            return 0
        posts = await self._fetch_pending_posts(limit)
        enriched = 0
        for item in posts:
            result = await self._enrich_and_persist(
                item["id"],
                item["post_text"],
                item["categories"],
                item["user_id"],
            )
            if result:
                enriched += 1
        return enriched

    async def _enrich_and_persist(
        self,
        post_id: int,
        text: str,
        categories: List[str],
        user_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            if user_id is not None and consume_ai_calls is not None:
                await consume_ai_calls(
                    int(user_id),
                    units=1,
                    acquire=get_db_connection,
                    release=release_db_connection,
                )
        except AiQuotaExceeded:
            _enrich_stats["skipped_quota"] = int(_enrich_stats["skipped_quota"]) + 1
            logger.info("Post enrichment skipped: AI quota exceeded user=%s", user_id)
            return None
        except Exception as exc:
            logger.warning("AI quota check failed, continuing: %s", exc)

        try:
            if not await ai_client.is_ready():
                logger.debug("Post enrichment skipped: AI not ready")
                return None
            started = time.perf_counter()
            enrichment = await ai_client.enrich(text, categories)
            latency_ms = (time.perf_counter() - started) * 1000
            self._record_latency(latency_ms)
            await self._update_post_metadata(post_id, enrichment)
            await self._update_collected_event_metadata(post_id, enrichment)
            _enrich_stats["enriched"] = int(_enrich_stats["enriched"]) + 1
            return enrichment
        except Exception as exc:
            _enrich_stats["errors"] = int(_enrich_stats["errors"]) + 1
            logger.warning("Post enrichment failed for post %s: %s", post_id, exc)
            return None

    @staticmethod
    def _parse_categories(raw: Any) -> List[str]:
        categories = raw or []
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = []
        if not isinstance(categories, list) or not categories:
            return ["новости", "реклама", "технологии", "финансы", "другое"]
        return [str(c).strip() for c in categories if str(c).strip()]

    @staticmethod
    def _record_latency(latency_ms: float) -> None:
        _enrich_stats["last_latency_ms"] = round(latency_ms, 1)
        _latency_samples.append(latency_ms)
        if len(_latency_samples) > 50:
            del _latency_samples[:-50]
        _enrich_stats["avg_latency_ms"] = round(
            sum(_latency_samples) / len(_latency_samples), 1
        )

    async def _fetch_pending_posts(self, limit: int) -> List[Dict[str, Any]]:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT p.id, p.user_id, p.post_text, pr.classification_categories
                        FROM posts p
                        JOIN tg_profiles pr ON pr.user_id = p.user_id
                        WHERE p.source_platform IN ('tg', 'telegram')
                          AND pr.batch_enrichment_enabled = TRUE
                          AND pr.classification_enabled = TRUE
                          AND p.post_text IS NOT NULL
                          AND length(trim(p.post_text)) > 0
                          AND (
                            p.extras IS NULL
                            OR NOT (COALESCE(p.extras->'metadata', '{}'::jsonb) ? 'sentiment')
                          )
                        ORDER BY p.created_at ASC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    rows = await cur.fetchall()
                    result = []
                    for post_id, user_id, post_text, categories in rows:
                        result.append(
                            {
                                "id": post_id,
                                "user_id": user_id,
                                "post_text": post_text or "",
                                "categories": self._parse_categories(categories),
                            }
                        )
                    return result
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to fetch posts for batch enrichment: %s", exc)
            return []

    async def _update_post_metadata(self, post_id: int, enrichment: Dict[str, Any]) -> None:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE posts
                        SET extras = jsonb_set(
                            COALESCE(extras, '{}'::jsonb),
                            '{metadata}',
                            COALESCE(extras->'metadata', '{}'::jsonb) || %s::jsonb
                        ),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (json.dumps(enrichment), post_id),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to update tg_posts metadata: %s", exc)

    async def _update_collected_event_metadata(
        self, post_id: int, enrichment: Dict[str, Any]
    ) -> None:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE tg_events
                        SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                        WHERE event_type = 'collected'
                          AND metadata->>'post_id' = %s
                        """,
                        (
                            json.dumps(
                                {
                                    "category": enrichment.get("category"),
                                    "sentiment": enrichment.get("sentiment"),
                                    "score": enrichment.get("score"),
                                    "confidence": enrichment.get("confidence"),
                                    "enriched": True,
                                }
                            ),
                            str(post_id),
                        ),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.warning("Failed to update tg_events metadata for post %s: %s", post_id, exc)
