"""AI-enrichment собранных tg_posts (category, sentiment)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore


class PostEnrichmentService:
    """Обогащает tg_posts метаданными через AI."""

    async def enrich_post_if_enabled(
        self,
        post_id: int,
        text: str,
        profile: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not ai_client:
            return None

        classification_enabled = profile.get("classification_enabled", False)
        categories = profile.get("classification_categories") or []
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = []

        if not classification_enabled or not text:
            return None

        try:
            if not await ai_client.is_ready():
                logger.debug("Post enrichment skipped: AI not ready")
                return None
            enrichment = await ai_client.enrich(text, categories)
            await self._update_post_metadata(post_id, enrichment)
            return enrichment
        except Exception as exc:
            logger.warning("Post enrichment failed for post %s: %s", post_id, exc)
            return None

    async def _update_post_metadata(self, post_id: int, enrichment: Dict[str, Any]) -> None:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE tg_posts
                        SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (json.dumps(enrichment), post_id),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to update tg_posts metadata: %s", exc)
