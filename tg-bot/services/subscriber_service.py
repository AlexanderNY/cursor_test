"""Daily subscriber count snapshots for SMM brand channels (Telegram)."""

from __future__ import annotations

import logging
from typing import Optional

from telethon.tl.functions.channels import GetFullChannelRequest

from database import get_db_connection, release_db_connection
from .client_manager import TelegramClientManager
from .channel_counter import record_subscriber_snapshot

logger = logging.getLogger(__name__)


class SubscriberService:
    def __init__(self, client_manager: TelegramClientManager):
        self.client_manager = client_manager

    async def sync_subscribers(self) -> int:
        channels = await self._list_tg_channels()
        updated = 0
        for channel_id, user_id, external_id in channels:
            client = self.client_manager.get_client(user_id)
            if client is None:
                continue
            count = await self._fetch_participants(client, external_id)
            if count is None:
                continue
            await record_subscriber_snapshot(channel_id, count)
            updated += 1
        return updated

    @staticmethod
    async def _list_tg_channels() -> list[tuple[int, int, str]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id, b.user_id, c.external_id
                    FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE c.network = 'tg'
                      AND c.external_id IS NOT NULL
                      AND TRIM(c.external_id) != ''
                    """
                )
                rows = await cur.fetchall()
                return [
                    (int(r[0]), int(r[1]), str(r[2]).strip())
                    for r in rows
                    if r[0] is not None and r[1] is not None and r[2]
                ]
        finally:
            await release_db_connection(conn)

    @staticmethod
    async def _fetch_participants(client, external_id: str) -> Optional[int]:
        try:
            entity = await client.get_entity(int(external_id))
            full = await client(GetFullChannelRequest(entity))
            participants = getattr(full.full_chat, "participants_count", None)
            if participants is None:
                return None
            return max(0, int(participants))
        except Exception as exc:
            logger.debug("TG subscriber fetch failed for %s: %s", external_id, exc)
            return None
