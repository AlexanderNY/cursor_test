"""Batch-дайджесты сообщений по каналам."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_db_connection, release_db_connection

from services.alert_service import parse_channel
from services.message_handler import MessageHandler

logger = logging.getLogger(__name__)

try:
    from shared import ai_client
except ImportError:
    ai_client = None  # type: ignore

DigestPost = Dict[str, Any]
ChatGroups = Dict[str, List[DigestPost]]

DEFAULT_DIGEST_SLEEP_SEC = 1800
MIN_DIGEST_INTERVAL_MIN = 5
MAX_DIGEST_INTERVAL_MIN = 1440


class SummaryAggregator:
    """Периодически формирует дайджесты по каналам."""

    def __init__(self) -> None:
        self._message_handler = MessageHandler()

    async def get_digest_sleep_interval_sec(self) -> int:
        """Интервал сна digest-loop: минимум digest_interval_min среди активных профилей."""
        profiles = await self._load_digest_profiles()
        if not profiles:
            return DEFAULT_DIGEST_SLEEP_SEC

        intervals = [
            max(
                MIN_DIGEST_INTERVAL_MIN,
                min(MAX_DIGEST_INTERVAL_MIN, int(profile.get("digest_interval_min") or 30)),
            )
            for profile in profiles
        ]
        return min(intervals) * 60

    async def run_digest_cycle(self, client_manager) -> int:
        if not ai_client:
            return 0

        profiles = await self._load_digest_profiles()
        digests_sent = 0

        for profile in profiles:
            user_id = profile["user_id"]
            interval_min = int(profile.get("digest_interval_min") or 30)
            digest_channel = (profile.get("digest_channel") or "").strip()
            digest_mode = (profile.get("digest_mode") or "per_channel").strip()
            chats_to_read = profile.get("chats_to_read") or []
            if not digest_channel:
                continue

            client = client_manager.get_client(user_id)
            if not client:
                continue

            chat_groups = await self._fetch_recent_posts(
                user_id=user_id,
                interval_min=interval_min,
                chats_to_read=chats_to_read,
            )
            if not chat_groups:
                continue

            channel = parse_channel(digest_channel)
            if channel is None:
                continue

            if digest_mode == "combined":
                digests_sent += await self._send_combined_digest(
                    client=client,
                    user_id=user_id,
                    channel=channel,
                    chat_groups=chat_groups,
                    interval_min=interval_min,
                )
                continue

            for chat_id, posts in chat_groups.items():
                if not posts:
                    continue
                texts = [post["text"] for post in posts]
                digest = await self._build_digest(texts, chat_id)
                if not digest:
                    continue
                post_ids = [post["id"] for post in posts]
                await self._save_digest(user_id, chat_id, digest, len(texts))
                try:
                    await client.send_message(
                        channel,
                        f"Дайджест канала {chat_id} ({len(texts)} сообщ.):\n\n{digest}",
                    )
                    await self._mark_posts_digested(post_ids)
                    digests_sent += 1
                except Exception as exc:
                    logger.error("Failed to send digest for user %s chat %s: %s", user_id, chat_id, exc)

        return digests_sent

    async def _send_combined_digest(
        self,
        client,
        user_id: int,
        channel: Any,
        chat_groups: ChatGroups,
        interval_min: int,
    ) -> int:
        total_messages = sum(len(posts) for posts in chat_groups.values())
        if total_messages == 0:
            return 0

        digest = await self._build_combined_digest(chat_groups, interval_min)
        if not digest:
            return 0

        all_post_ids = [post["id"] for posts in chat_groups.values() for post in posts]
        await self._save_digest(user_id, "combined", digest, total_messages)
        try:
            await client.send_message(
                channel,
                (
                    f"Сводка за {interval_min} мин. "
                    f"({total_messages} сообщ. из {len(chat_groups)} каналов):\n\n{digest}"
                ),
            )
            await self._mark_posts_digested(all_post_ids)
            return 1
        except Exception as exc:
            logger.error("Failed to send combined digest for user %s: %s", user_id, exc)
            return 0

    async def _load_digest_profiles(self) -> List[Dict[str, Any]]:
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT user_id, digest_interval_min, digest_channel, digest_mode,
                               chats_to_read, summarize_enabled
                        FROM tg_profiles
                        WHERE summarize_enabled = TRUE AND digest_channel IS NOT NULL
                          AND digest_channel != ''
                        """
                    )
                    rows = await cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    profiles = [dict(zip(cols, row)) for row in rows]
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to load digest profiles: %s", exc)
            return []

        for profile in profiles:
            chats = profile.get("chats_to_read")
            if isinstance(chats, str):
                try:
                    profile["chats_to_read"] = json.loads(chats)
                except (json.JSONDecodeError, TypeError):
                    profile["chats_to_read"] = []
            elif not isinstance(chats, list):
                profile["chats_to_read"] = []

        return profiles

    async def _fetch_recent_posts(
        self,
        user_id: int,
        interval_min: int,
        chats_to_read: List[str],
    ) -> ChatGroups:
        since = datetime.utcnow() - timedelta(minutes=interval_min)
        result: ChatGroups = {}
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT id, domain, post_text, metadata FROM tg_posts
                        WHERE user_id = %s AND status = 'collected'
                          AND created_at > %s AND post_text IS NOT NULL
                          AND COALESCE(metadata->>'digested_at', '') = ''
                        ORDER BY created_at
                        """,
                        (user_id, since),
                    )
                    rows = await cur.fetchall()
                    for post_id, domain, post_text, metadata in rows:
                        chat_key = str(domain or "unknown")
                        if chats_to_read and not self._domain_in_chats(chat_key, chats_to_read):
                            continue
                        if self._is_post_digested(metadata):
                            continue
                        result.setdefault(chat_key, []).append(
                            {"id": post_id, "text": post_text}
                        )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to fetch posts for digest: %s", exc)
        return result

    def _domain_in_chats(self, domain: str, chats_to_read: List[str]) -> bool:
        try:
            chat_id = int(domain)
        except (TypeError, ValueError):
            return domain in [str(chat) for chat in chats_to_read]
        return self._message_handler.chat_id_in_list(chat_id, chats_to_read)

    @staticmethod
    def _is_post_digested(metadata: Any) -> bool:
        if not metadata:
            return False
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                return False
        if not isinstance(metadata, dict):
            return False
        return bool(metadata.get("digested_at"))

    async def _mark_posts_digested(self, post_ids: List[int]) -> None:
        if not post_ids:
            return
        digested_at = datetime.utcnow().isoformat()
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    ids_placeholder = ", ".join(["%s"] * len(post_ids))
                    await cur.execute(
                        f"""
                        UPDATE tg_posts
                        SET metadata = COALESCE(metadata, '{{}}'::jsonb)
                            || jsonb_build_object('digested_at', %s),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({ids_placeholder})
                        """,
                        [digested_at, *post_ids],
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to mark posts as digested: %s", exc)

    async def _build_digest(self, texts: List[str], chat_id: str) -> Optional[str]:
        combined = "\n---\n".join(texts[:20])
        if len(combined) > 8000:
            combined = combined[:8000]
        prompt = (
            f"Сделай краткий дайджест из {len(texts)} сообщений канала {chat_id}. "
            f"Выдели главные темы и факты:\n\n{combined}"
        )
        try:
            return await ai_client.complete(prompt, system="Ты редактор дайджестов.", max_tokens=1024)
        except Exception as exc:
            logger.warning("Digest generation failed: %s", exc)
            return None

    async def _build_combined_digest(
        self,
        chat_groups: ChatGroups,
        interval_min: int,
    ) -> Optional[str]:
        sections: List[str] = []
        total = 0
        for chat_id, posts in chat_groups.items():
            texts = [post["text"] for post in posts[:20]]
            total += len(posts)
            section_body = "\n".join(f"- {text}" for text in texts)
            if len(section_body) > 2000:
                section_body = section_body[:2000]
            sections.append(f"Канал {chat_id} ({len(posts)} сообщ.):\n{section_body}")

        combined = "\n\n".join(sections)
        if len(combined) > 8000:
            combined = combined[:8000]
        prompt = (
            f"Сделай единую сводку за {interval_min} минут по {total} сообщениям "
            f"из {len(chat_groups)} каналов. Выдели главные темы и факты по каждому каналу:\n\n"
            f"{combined}"
        )
        try:
            return await ai_client.complete(prompt, system="Ты редактор дайджестов.", max_tokens=1024)
        except Exception as exc:
            logger.warning("Combined digest generation failed: %s", exc)
            return None

    async def _save_digest(self, user_id: int, chat_id: str, digest_text: str, count: int) -> None:
        stored_chat_id = 0
        if chat_id != "combined" and str(chat_id).lstrip("-").isdigit():
            stored_chat_id = int(chat_id)
        try:
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO tg_digests (user_id, chat_id, digest_text, message_count)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (user_id, stored_chat_id, digest_text, count),
                    )
            finally:
                await release_db_connection(conn)
        except Exception as exc:
            logger.error("Failed to save digest: %s", exc)
