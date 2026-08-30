"""Сбор постов со стен VK: brand channels (+ groups_to_read fallback) → vk_posts + alerts."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from database import get_db_connection, release_db_connection
from config import settings
from shared.text_conditions import should_save_text
from .vk_client import VkClient
from .channel_counter import bump_channel_counter
from .brand_channel_flow import (
    channel_alert_rules_as_dispatch_rules,
    external_id_to_owner_id,
    list_vk_flow_channels,
    publish_targets_to_destination_fields,
    resolve_publish_targets,
)
from .alert_dispatcher import dispatch_alerts_for_post


logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


class PostCollector:
    """Сбор: brand VK channels (primary) + vk_profiles.groups_to_read / users_to_read (fallback)."""

    async def get_profiles_for_token(self) -> Dict[int, Dict]:
        """user_id → tokens (any profile with a usable token)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, access_token, user_access_token,
                           collect_enabled, groups_to_read, users_to_read
                    FROM vk_profiles
                    WHERE (
                        (user_access_token IS NOT NULL AND user_access_token != '')
                        OR (access_token IS NOT NULL AND access_token != '')
                      )
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                result: Dict[int, Dict] = {}
                for row in rows:
                    rec = dict(zip(cols, row))
                    for key in ("groups_to_read", "users_to_read"):
                        val = rec.get(key)
                        if isinstance(val, str):
                            try:
                                rec[key] = json.loads(val)
                            except (json.JSONDecodeError, TypeError):
                                rec[key] = []
                        if rec.get(key) is None:
                            rec[key] = []
                    result[int(rec["user_id"])] = rec
                return result
        finally:
            await release_db_connection(conn)

    async def get_max_source_id(self, user_id: int, domain: str) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COALESCE(MAX(vk_source_id), 0)
                    FROM vk_posts
                    WHERE user_id = %s AND domain = %s
                    """,
                    (user_id, domain),
                )
                row = await cur.fetchone()
                posts_max = int((row[0] or 0) if row else 0)
                cursor_max = 0
                try:
                    await cur.execute(
                        """
                        SELECT last_source_id FROM vk_wall_cursors
                        WHERE user_id = %s AND domain = %s
                        """,
                        (user_id, domain),
                    )
                    crow = await cur.fetchone()
                    cursor_max = int((crow[0] or 0) if crow else 0)
                except Exception:
                    cursor_max = 0
                return max(posts_max, cursor_max)
        finally:
            await release_db_connection(conn)

    async def advance_cursor(self, user_id: int, domain: str, last_source_id: int) -> None:
        if last_source_id <= 0:
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_wall_cursors (user_id, domain, last_source_id, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, domain) DO UPDATE
                    SET last_source_id = GREATEST(vk_wall_cursors.last_source_id, EXCLUDED.last_source_id),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, domain, int(last_source_id)),
                )
        except Exception as exc:
            logger.debug("advance_cursor skipped: %s", exc)
        finally:
            await release_db_connection(conn)

    def _parse_group_owner_id(self, group_id: Any) -> Optional[int]:
        return external_id_to_owner_id(str(group_id), as_user=False)

    def _parse_user_owner_id(self, user_id: Any) -> Optional[int]:
        return external_id_to_owner_id(str(user_id), as_user=True)

    def _item_to_row(
        self,
        user_id: int,
        owner_id: int,
        item: Dict[str, Any],
    ) -> Optional[tuple]:
        try:
            post_id = item.get("id")
            text = (item.get("text") or "")[:16384]
            ts = item.get("date")
            post_date = datetime.utcfromtimestamp(ts) if ts else None
            from_id = item.get("from_id")
            author = str(from_id) if from_id is not None else None
            if author and len(author) > 255:
                author = author[:255]
            comments = (item.get("comments") or {}).get("count", 0) or 0
            likes = (item.get("likes") or {}).get("count", 0) or 0
            reposts = (item.get("reposts") or {}).get("count", 0) or 0
            views = (
                (item.get("views") or {}).get("count", 0)
                if isinstance(item.get("views"), dict)
                else (item.get("views") or 0)
            )
            domain = str(owner_id)
            images: List[str] = []
            for att in item.get("attachments") or []:
                if att.get("type") == "photo":
                    photo = att.get("photo") or {}
                    url = None
                    for key in [
                        "photo_2560",
                        "photo_1280",
                        "photo_807",
                        "photo_604",
                        "photo_130",
                    ]:
                        if photo.get(key):
                            url = photo[key]
                            break
                    if url:
                        images.append(url)
            return (
                user_id,
                post_id,
                domain,
                text,
                post_date,
                author,
                json.dumps(images),
                comments,
                reposts,
                likes,
                views,
            )
        except Exception as e:
            logger.debug("_item_to_row skip item: %s", e)
            return None

    async def save_post(
        self,
        user_id: int,
        vk_source_id: int,
        domain: str,
        post_text: str,
        post_date: Optional[datetime],
        author: Optional[str],
        images_json: str,
        comments: int,
        reposts: int,
        likes: int,
        views: int,
        *,
        dest: Optional[Dict[str, Any]] = None,
    ) -> bool:
        dest = dest or {}
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO vk_posts (
                        user_id, vk_source_id, domain, post_text, post_date, author,
                        images, comments, reposts, likes, views,
                        status, post_type,
                        to_tg, to_tw, to_wp, to_vk, to_threads, to_dzen, to_instagram,
                        target_channels, target_groups,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'collected', 'vk',
                        %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                    """,
                    (
                        user_id,
                        vk_source_id,
                        domain,
                        post_text,
                        post_date,
                        author,
                        images_json,
                        comments,
                        reposts,
                        likes,
                        views,
                        bool(dest.get("to_tg")),
                        bool(dest.get("to_tw")),
                        bool(dest.get("to_wp")),
                        bool(dest.get("to_vk")),
                        bool(dest.get("to_threads")),
                        bool(dest.get("to_dzen")),
                        bool(dest.get("to_instagram")),
                        json.dumps(dest.get("target_channels") or []),
                        json.dumps(dest.get("target_groups") or []),
                    ),
                )
                row = await cur.fetchone()
                post_row_id = int(row[0]) if row else None
                _log_action(
                    "Saved vk post user_id=%s domain=%s vk_source_id=%s to_tg=%s to_vk=%s",
                    user_id,
                    domain,
                    vk_source_id,
                    bool(dest.get("to_tg")),
                    bool(dest.get("to_vk")),
                )
                if post_row_id:
                    await bump_channel_counter(
                        user_id,
                        network="vk",
                        external_id=domain,
                        received=1,
                        direction="collected",
                        platform="vk",
                        post_id=post_row_id,
                        metadata={"text_preview": (post_text or "")[:120]},
                    )
                return True
        except Exception as e:
            logger.error("Error saving vk post: %s", e, exc_info=True)
            return False
        finally:
            await release_db_connection(conn)

    async def _dest_for_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = channel.get("brand_id")
        target_ids = channel.get("publish_targets") or []
        if not brand_id or not target_ids:
            return {}
        resolved = await resolve_publish_targets(int(brand_id), target_ids)
        return publish_targets_to_destination_fields(resolved)

    async def _alert_rules_for_channel(self, channel: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not channel.get("alert_enabled"):
            return []
        delivery = channel.get("alert_delivery") or {}
        target_ids = []
        if isinstance(delivery, dict):
            raw = delivery.get("alert_targets") or []
            if isinstance(raw, list):
                for x in raw:
                    try:
                        target_ids.append(int(x))
                    except (TypeError, ValueError):
                        continue
        destinations: List[Dict[str, Any]] = []
        brand_id = channel.get("brand_id")
        if brand_id and target_ids:
            destinations = await resolve_publish_targets(int(brand_id), target_ids)
        return channel_alert_rules_as_dispatch_rules(channel, destinations)

    async def _poll_wall(
        self,
        *,
        user_id: int,
        client: VkClient,
        owner_id: int,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
        collect_enabled: bool = True,
        dest: Optional[Dict[str, Any]] = None,
        alert_rules: Optional[List[Dict[str, Any]]] = None,
        source_external_id: str = "",
    ) -> int:
        domain = str(owner_id)
        max_id = await self.get_max_source_id(user_id, domain)
        items = await client.wall_get(owner_id=owner_id, count=20)
        saved = 0
        batch_max = max_id
        for item in items:
            post_id = item.get("id")
            if post_id is None or post_id <= max_id:
                continue
            if int(post_id) > batch_max:
                batch_max = int(post_id)
            row = self._item_to_row(user_id, owner_id, item)
            if not row:
                continue
            (
                uid,
                vk_source_id,
                dom,
                post_text,
                post_date,
                author,
                images_json,
                comments,
                reposts,
                likes,
                views,
            ) = row

            if alert_rules:
                await dispatch_alerts_for_post(
                    uid,
                    alert_rules,
                    source_external_id=source_external_id or dom,
                    source_domain=dom,
                    post_text=post_text or "",
                    vk_source_id=int(vk_source_id) if vk_source_id is not None else None,
                )

            if not collect_enabled:
                continue
            if not should_save_text(
                post_text or "",
                save_conditions or [],
                conditions_mode or "any_of",
            ):
                continue

            ok = await self.save_post(
                uid,
                vk_source_id,
                dom,
                post_text,
                post_date,
                author,
                images_json,
                comments,
                reposts,
                likes,
                views,
                dest=dest,
            )
            if ok:
                saved += 1
        if batch_max > max_id:
            await self.advance_cursor(user_id, domain, batch_max)
        return saved

    async def run_collect(self) -> int:
        profiles = await self.get_profiles_for_token()
        if not profiles:
            return 0

        channels = await list_vk_flow_channels()
        saved = 0
        polled: Set[Tuple[int, int]] = set()  # (user_id, owner_id)

        # --- Brand channels (primary) ---
        for channel in channels:
            user_id = int(channel["user_id"])
            profile = profiles.get(user_id)
            if not profile:
                continue
            # wall.get for foreign/own walls needs user OAuth (community token → API error 27)
            token = (profile.get("user_access_token") or "").strip()
            if not token:
                logger.debug(
                    "Skip VK brand channel user=%s: user_access_token required for collect/alert",
                    user_id,
                )
                continue
            owner_id = self._parse_group_owner_id(channel.get("external_id"))
            if owner_id is None:
                continue

            dest: Dict[str, Any] = {}
            if channel.get("collect_enabled"):
                dest = await self._dest_for_channel(channel)
            alert_rules = await self._alert_rules_for_channel(channel)

            client = VkClient(token)
            n = await self._poll_wall(
                user_id=user_id,
                client=client,
                owner_id=owner_id,
                save_conditions=channel.get("save_conditions") or [],
                conditions_mode=channel.get("conditions_mode") or "any_of",
                collect_enabled=bool(channel.get("collect_enabled")),
                dest=dest,
                alert_rules=alert_rules,
                source_external_id=str(channel.get("external_id") or ""),
            )
            saved += n
            polled.add((user_id, owner_id))

        # --- Profile fallback: groups_to_read / users_to_read ---
        for user_id, profile in profiles.items():
            if not profile.get("collect_enabled"):
                continue
            token = (profile.get("user_access_token") or "").strip()
            if not token:
                logger.debug(
                    "Skip VK profile collect user=%s: user_access_token required",
                    user_id,
                )
                continue
            client = VkClient(token)
            for g in profile.get("groups_to_read") or []:
                owner_id = self._parse_group_owner_id(g)
                if owner_id is None or (user_id, owner_id) in polled:
                    continue
                n = await self._poll_wall(
                    user_id=user_id,
                    client=client,
                    owner_id=owner_id,
                    collect_enabled=True,
                    source_external_id=str(g),
                )
                saved += n
                polled.add((user_id, owner_id))
            for u in profile.get("users_to_read") or []:
                owner_id = self._parse_user_owner_id(u)
                if owner_id is None or (user_id, owner_id) in polled:
                    continue
                n = await self._poll_wall(
                    user_id=user_id,
                    client=client,
                    owner_id=owner_id,
                    collect_enabled=True,
                    source_external_id=str(u),
                )
                saved += n
                polled.add((user_id, owner_id))

        return saved
