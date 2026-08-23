"""Daily subscriber count snapshots for SMM brand channels (VK)."""

from __future__ import annotations

import logging
from typing import Optional

from database import get_db_connection, release_db_connection
from .vk_client import VkClient
from .channel_counter import record_subscriber_snapshot

logger = logging.getLogger(__name__)


class VkSubscriberService:
    async def sync_subscribers(self) -> int:
        rows = await self._list_vk_channels()
        updated = 0
        for channel_id, external_id, access_token, user_token in rows:
            client = self._client_for_group(external_id, access_token, user_token)
            if client is None:
                continue
            count = await self._fetch_members(client, external_id)
            if count is None:
                continue
            await record_subscriber_snapshot(channel_id, count)
            updated += 1
        return updated

    @staticmethod
    async def _list_vk_channels() -> list[tuple[int, str, Optional[str], Optional[str]]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id, c.external_id, p.access_token, p.user_access_token
                    FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    JOIN vk_profiles p ON p.user_id = b.user_id
                    WHERE c.network = 'vk'
                      AND c.external_id IS NOT NULL
                      AND TRIM(c.external_id) != ''
                    """
                )
                rows = await cur.fetchall()
                return [
                    (int(r[0]), str(r[1]).strip(), r[2], r[3])
                    for r in rows
                    if r[0] is not None and r[1]
                ]
        finally:
            await release_db_connection(conn)

    @staticmethod
    def _client_for_group(
        external_id: str,
        access_token: Optional[str],
        user_access_token: Optional[str],
    ) -> Optional[VkClient]:
        ext = external_id.lstrip("-")
        try:
            group_id = int(ext)
        except (TypeError, ValueError):
            return None
        if group_id > 0 and access_token:
            return VkClient(access_token)
        if user_access_token:
            return VkClient(user_access_token)
        if access_token:
            return VkClient(access_token)
        return None

    @staticmethod
    async def _fetch_members(client: VkClient, external_id: str) -> Optional[int]:
        ext = external_id.lstrip("-")
        try:
            group_id = int(ext)
        except (TypeError, ValueError):
            return None
        try:
            items = await client.groups_get_by_id([str(group_id)])
            if not items:
                return None
            members = items[0].get("members_count")
            if members is None:
                return None
            return max(0, int(members))
        except Exception as exc:
            logger.debug("VK subscriber fetch failed for %s: %s", external_id, exc)
            return None
