"""
Сбор постов Instagram в posts.

Приоритет:
1) Brand channels (network=instagram, collect_enabled) — @username через instagrapi
2) Legacy: usernames_to_read + свой аккаунт при collect_enabled на профиле
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from database import get_db_connection, release_db_connection
from config import settings
from shared.db.bot_queue import dest_flags_to_platforms
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http
from shared.text_conditions import should_save_text

from .brand_channel_flow import (
    list_instagram_flow_channels,
    normalize_instagram_handle,
    publish_targets_to_destination_fields,
    resolve_publish_targets,
)
from .channel_counter import bump_channel_counter
from .image_mirror import mirror_collected_images_to_storage
from .instagram_client import InstagramClient

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _normalize_session(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


class PostCollector:
    """Brand-channel usernames + legacy usernames_to_read / own feed."""

    async def _profiles_map(self) -> Dict[int, Dict[str, Any]]:
        """Profiles with credentials (for brand collect and/or legacy)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, username, password, usernames_to_read,
                           instagrapi_session, instagram_verification_code,
                           collect_enabled
                    FROM instagram_profiles
                    WHERE username IS NOT NULL AND username != ''
                      AND password IS NOT NULL AND password != ''
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                result: Dict[int, Dict[str, Any]] = {}
                for row in rows:
                    rec = dict(zip(cols, row))
                    if isinstance(rec.get("usernames_to_read"), str):
                        try:
                            rec["usernames_to_read"] = json.loads(rec["usernames_to_read"])
                        except (json.JSONDecodeError, TypeError):
                            rec["usernames_to_read"] = []
                    if rec.get("usernames_to_read") is None:
                        rec["usernames_to_read"] = []
                    rec["instagrapi_session"] = _normalize_session(rec.get("instagrapi_session"))
                    result[int(rec["user_id"])] = rec
                return result
        finally:
            await release_db_connection(conn)

    async def _dest_for_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = channel.get("brand_id")
        target_ids = channel.get("publish_targets") or []
        if not brand_id or not target_ids:
            return {}
        resolved = await resolve_publish_targets(int(brand_id), target_ids)
        return publish_targets_to_destination_fields(resolved)

    async def exists_by_source_id(self, user_id: int, domain: str, source_id: str) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 1 FROM posts
                    WHERE user_id = %s AND source_platform = 'instagram'
                      AND source_native_id = %s
                    LIMIT 1
                    """,
                    (user_id, f"{domain}:{source_id}"),
                )
                row = await cur.fetchone()
                return row is not None
        finally:
            await release_db_connection(conn)

    async def save_post(
        self,
        user_id: int,
        instagram_source_id: str,
        domain: str,
        post_text: str,
        post_date: Optional[datetime],
        author: Optional[str],
        images_json: str,
        comments: int,
        likes: int,
        *,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
    ) -> Optional[int]:
        body = (post_text or "").strip()
        if not should_save_text(body, save_conditions or [], conditions_mode or "any_of"):
            return None
        dest = dest or {}
        platforms = dest_flags_to_platforms(dest)
        if not platforms:
            platforms = ("instagram",)
        images = json.loads(images_json) if isinstance(images_json, str) else images_json
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                created = await PostsRepository(cur).create_inbound(
                    InboundPostCreate(
                        user_id=user_id,
                        source_platform="instagram",
                        post_text=body,
                        post_date=post_date,
                        author=author,
                        domain=domain,
                        brand_id=brand_id,
                        channel_id=channel_id,
                        images=images if isinstance(images, list) else [],
                        extras={
                            "instagram_source_id": str(instagram_source_id),
                            "comments": comments,
                            "likes": likes,
                        },
                        source_native_id=f"{domain}:{instagram_source_id}",
                        target_channels=dest.get("target_channels") or [],
                        target_groups=dest.get("target_groups") or [],
                        target_platforms=platforms,
                        target_status="pending",
                    )
                )
                new_id = int(created["id"])
                _log_action(
                    "Saved instagram post id=%s user_id=%s domain=%s source_id=%s brand=%s channel=%s",
                    new_id,
                    user_id,
                    domain,
                    instagram_source_id,
                    brand_id,
                    channel_id,
                )
            if channel_id is not None or domain:
                await bump_channel_counter(
                    user_id,
                    network="instagram",
                    external_id=domain,
                    channel_id=channel_id,
                    received=1,
                    direction="collected",
                    platform="instagram",
                    post_id=new_id,
                    external_msg_id=str(instagram_source_id),
                    metadata={"text_preview": body[:120]},
                )
            await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
            return new_id
        except Exception as e:
            logger.error("Error saving instagram post: %s", e, exc_info=True)
            return None
        finally:
            await release_db_connection(conn)

    def _taken_at(self, m: Dict[str, Any]) -> Optional[datetime]:
        post_date = m.get("taken_at")
        if isinstance(post_date, datetime):
            return post_date
        if post_date and hasattr(post_date, "timestamp"):
            return datetime.utcfromtimestamp(post_date.timestamp())
        return None

    async def _save_media_items(
        self,
        user_id: int,
        domain: str,
        author: str,
        medias: List[Dict[str, Any]],
        *,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
    ) -> int:
        saved = 0
        for m in medias:
            pk = m.get("pk") or m.get("id")
            if not pk:
                continue
            source_id = str(pk)
            if await self.exists_by_source_id(user_id, domain, source_id):
                continue
            images_list = m.get("images") or []
            images_json = json.dumps(images_list)
            new_id = await self.save_post(
                user_id=user_id,
                instagram_source_id=source_id,
                domain=domain,
                post_text=(m.get("caption") or "")[:2200],
                post_date=self._taken_at(m),
                author=author,
                images_json=images_json,
                comments=m.get("comment_count") or 0,
                likes=m.get("like_count") or 0,
                dest=dest,
                brand_id=brand_id,
                channel_id=channel_id,
                save_conditions=save_conditions,
                conditions_mode=conditions_mode,
            )
            if new_id is not None:
                saved += 1
                if images_list and getattr(settings, "COLLECT_MIRROR_IMAGES_TO_S3", True):
                    await mirror_collected_images_to_storage(new_id, user_id, images_list)
        return saved

    async def _client_for_profile(self, profile: Dict[str, Any]) -> Optional[InstagramClient]:
        username = (profile.get("username") or "").strip()
        password = profile.get("password") or ""
        if not username or not password:
            return None
        client = InstagramClient(
            username,
            password,
            user_id=int(profile["user_id"]),
            session_dict=profile.get("instagrapi_session"),
            verification_code=profile.get("instagram_verification_code"),
        )
        if not await client.login():
            logger.warning("Instagram login failed for user_id=%s", profile.get("user_id"))
            return None
        return client

    async def _collect_username(
        self,
        client: InstagramClient,
        user_id: int,
        handle: str,
        *,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
    ) -> int:
        if handle.isdigit():
            uid: Optional[int] = int(handle)
            domain = handle
            author = handle
        else:
            uid = await client.user_id_from_username(handle)
            domain = handle
            author = handle
        if uid is None:
            logger.debug("Instagram user not found: @%s", handle)
            return 0
        medias = await client.user_medias(uid, amount=20)
        return await self._save_media_items(
            user_id,
            domain,
            author,
            medias,
            dest=dest,
            brand_id=brand_id,
            channel_id=channel_id,
            save_conditions=save_conditions,
            conditions_mode=conditions_mode,
        )

    async def run_collect(self) -> int:
        profiles = await self._profiles_map()
        if not profiles:
            return 0

        total = 0
        polled: Set[Tuple[int, str]] = set()
        clients: Dict[int, InstagramClient] = {}

        async def _ensure_client(uid: int) -> Optional[InstagramClient]:
            if uid in clients:
                return clients[uid]
            pr = profiles.get(uid)
            if not pr:
                return None
            client = await self._client_for_profile(pr)
            if client:
                clients[uid] = client
            return client

        channels = await list_instagram_flow_channels()
        for channel in channels:
            user_id = int(channel["user_id"])
            handle = normalize_instagram_handle(str(channel.get("external_id") or ""))
            if not handle:
                logger.warning(
                    "Skip IG brand channel %s: bad external_id=%r",
                    channel.get("id"),
                    channel.get("external_id"),
                )
                continue
            key = (user_id, handle.lower())
            if key in polled:
                continue
            client = await _ensure_client(user_id)
            if not client:
                continue
            dest = await self._dest_for_channel(channel)
            brand_id = (
                int(channel["brand_id"]) if channel.get("brand_id") is not None else None
            )
            channel_id = int(channel["id"]) if channel.get("id") is not None else None
            try:
                n = await self._collect_username(
                    client,
                    user_id,
                    handle,
                    dest=dest,
                    brand_id=brand_id,
                    channel_id=channel_id,
                    save_conditions=channel.get("save_conditions") or [],
                    conditions_mode=channel.get("conditions_mode") or "any_of",
                )
                total += n
            except Exception as exc:
                logger.exception(
                    "collect brand channel user=%s @%s: %s", user_id, handle, exc
                )
            polled.add(key)

        # Legacy profile collect
        for user_id, profile in profiles.items():
            if not profile.get("collect_enabled"):
                continue
            client = await _ensure_client(user_id)
            if not client:
                continue
            username = (profile.get("username") or "").strip()
            try:
                self_uid = await client.get_self_user_id()
                if self_uid and username:
                    key = (user_id, username.lower())
                    if key not in polled:
                        medias = await client.user_medias(self_uid, amount=20)
                        total += await self._save_media_items(
                            user_id, username, username, medias
                        )
                        polled.add(key)
                for uname in profile.get("usernames_to_read") or []:
                    handle = normalize_instagram_handle(str(uname or ""))
                    if not handle:
                        continue
                    key = (user_id, handle.lower())
                    if key in polled:
                        continue
                    total += await self._collect_username(client, user_id, handle)
                    polled.add(key)
            except Exception as exc:
                logger.exception("legacy collect user=%s: %s", user_id, exc)

        return total
