"""Batch-дайджесты сообщений по каналам."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

from services.alert_service import parse_channel

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
    "skipped_quota": 0,
    "errors": 0,
    "last_latency_ms": None,
}


def get_digest_stats() -> Dict[str, Any]:
    return dict(_digest_stats)


class SummaryAggregator:
    """Периодически формирует дайджесты по каналам."""

    async def run_digest_cycle(self, client_manager) -> int:
        if not ai_client:
            return 0

        profiles = await self._load_digest_profiles()
        digests_sent = 0

        for profile in profiles:
            user_id = profile["user_id"]
            interval_min = int(profile.get("digest_interval_min") or 30)
            digest_channel = (profile.get("digest_channel") or "").strip()
            if not digest_channel:
                continue

            client = client_manager.get_client(user_id)
            if not client:
                continue

            chat_groups = await self._fetch_recent_posts(user_id, interval_min)
            for chat_id, texts in chat_groups.items():
                if not texts:
                    continue
                digest = await self._build_digest(texts, chat_id, user_id=user_id)
                if not digest:
                    continue
                await self._save_digest(user_id, chat_id, digest, len(texts))
                channel = parse_channel(digest_channel)
                if channel is not None:
                    try:
                        await client.send_message(
                            channel,
                            f"Дайджест канала {chat_id} ({len(texts)} сообщ.):\n\n{digest}",
                        )
                        digests_sent += 1
                        _digest_stats["sent"] = int(_digest_stats["sent"]) + 1
                    except Exception as exc:
                        _digest_stats["errors"] = int(_digest_stats["errors"]) + 1
                        logger.error("Failed to send digest for user %s: %s", user_id, exc)

        return digests_sent

    async def _load_digest_profiles(self) -> List[Dict[str, Any]]:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT user_id, digest_interval_min, digest_channel, summarize_enabled
                        FROM tg_profiles
                        WHERE summarize_enabled = TRUE AND digest_channel IS NOT NULL
                          AND digest_channel != ''
                        """
                    )
                    rows = await cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, row)) for row in rows]
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to load digest profiles: %s", exc)
            return []

    async def _fetch_recent_posts(
        self,
        user_id: int,
        interval_min: int,
    ) -> Dict[str, List[str]]:
        since = datetime.utcnow() - timedelta(minutes=interval_min)
        result: Dict[str, List[str]] = {}
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT domain, post_text FROM tg_posts
                        WHERE user_id = %s AND status = 'collected'
                          AND created_at > %s AND post_text IS NOT NULL
                        ORDER BY created_at
                        """,
                        (user_id, since),
                    )
                    rows = await cur.fetchall()
                    for domain, post_text in rows:
                        chat_key = str(domain or "unknown")
                        result.setdefault(chat_key, []).append(post_text)
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to fetch posts for digest: %s", exc)
        return result

    async def _build_digest(
        self,
        texts: List[str],
        chat_id: str,
        *,
        user_id: Optional[int] = None,
    ) -> Optional[str]:
        if user_id is not None and consume_ai_calls is not None:
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

        combined = "\n---\n".join(texts[:20])
        if len(combined) > 8000:
            combined = combined[:8000]
        prompt = (
            f"Сделай краткий дайджест из {len(texts)} сообщений канала {chat_id}. "
            f"Выдели главные темы и факты:\n\n{combined}"
        )
        try:
            started = time.perf_counter()
            result = await ai_client.complete(
                prompt, system="Ты редактор дайджестов.", max_tokens=1024
            )
            _digest_stats["last_latency_ms"] = round(
                (time.perf_counter() - started) * 1000, 1
            )
            return result
        except Exception as exc:
            _digest_stats["errors"] = int(_digest_stats["errors"]) + 1
            logger.warning("Digest generation failed: %s", exc)
            return None

    async def _save_digest(self, user_id: int, chat_id: str, digest_text: str, count: int) -> None:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_digests (user_id, chat_id, digest_text, message_count)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            int(chat_id) if chat_id.lstrip("-").isdigit() else 0,
                            digest_text,
                            count,
                        ),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to save digest: %s", exc)
