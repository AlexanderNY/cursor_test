"""
Сбор постов Threads в posts.

Приоритет:
1) Brand channels (network=threads, collect_enabled) — профиль @handle
   - браузер threads.net/@handle (основной путь для чужих аккаунтов)
   - API: свои посты / profile_lookup + threads (если Meta отдаёт)
2) Legacy: threads_profiles.collect_enabled → свои посты через OAuth API
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from config import settings
from database import get_db_connection, release_db_connection
from shared.db.bot_queue import dest_flags_to_platforms
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http
from shared.text_conditions import should_save_text

from .brand_channel_flow import (
    list_threads_flow_channels,
    normalize_threads_handle,
    publish_targets_to_destination_fields,
    resolve_publish_targets,
)
from .channel_counter import bump_channel_counter
from .threads_api import (
    canonical_thread_url,
    fetch_user_threads,
    lookup_profile_by_username,
)
from .threads_feed_browser import (
    collect_user_timeline_for_profile,
    extract_post_id,
)
from .selenium_diag_upload import upload_selenium_diagnostic_png

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if getattr(settings, "LOG_BOT_ACTIONS", False):
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _has_oauth(pr: Dict[str, Any]) -> bool:
    return bool((pr.get("access_token") or "").strip())


def _browser_creds(pr: Dict[str, Any]) -> Tuple[str, str]:
    login = (pr.get("meta_login") or pr.get("ig_username") or "").strip()
    password = pr.get("meta_password") or pr.get("ig_password") or ""
    if isinstance(password, str):
        password = password.strip()
    else:
        password = ""
    if login.startswith("@"):
        login = login[1:].strip()
    return login, password


def _has_browser_creds(pr: Dict[str, Any]) -> bool:
    login, password = _browser_creds(pr)
    return bool(login and password)


def _own_handle(pr: Dict[str, Any]) -> str:
    return normalize_threads_handle(str(pr.get("instagram_handle") or "")) or ""


class FeedCollector:
    """Brand-channel timelines + legacy own API collect."""

    async def _profiles_map(self) -> Dict[int, Dict[str, Any]]:
        conn = await get_db_connection()
        try:
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT t.user_id, t.access_token, t.threads_user_id, t.instagram_handle,
                               t.meta_login, t.meta_password, t.session_cookies,
                               t.collect_enabled, t.take_screenshot_collect,
                               i.username AS ig_username, i.password AS ig_password
                        FROM threads_profiles t
                        LEFT JOIN instagram_profiles i ON i.user_id = t.user_id
                        WHERE (
                            (t.access_token IS NOT NULL AND t.access_token != '')
                            OR (
                                t.meta_password IS NOT NULL AND t.meta_password != ''
                                AND t.meta_login IS NOT NULL AND t.meta_login != ''
                            )
                            OR (
                                i.password IS NOT NULL AND i.password != ''
                                AND i.username IS NOT NULL AND i.username != ''
                            )
                        )
                        """
                    )
                    rows = await cur.fetchall()
                    cols = [c.name for c in cur.description]
                    return {
                        int(dict(zip(cols, row))["user_id"]): dict(zip(cols, row))
                        for row in rows
                    }
            except Exception as exc:
                logger.debug("profiles_map join failed (%s), retry threads only", exc)
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT user_id, access_token, threads_user_id, instagram_handle,
                               meta_login, meta_password, session_cookies,
                               collect_enabled, take_screenshot_collect
                        FROM threads_profiles
                        WHERE (
                            (access_token IS NOT NULL AND access_token != '')
                            OR (
                                meta_password IS NOT NULL AND meta_password != ''
                                AND meta_login IS NOT NULL AND meta_login != ''
                            )
                        )
                        """
                    )
                    rows = await cur.fetchall()
                    cols = [c.name for c in cur.description]
                    return {
                        int(dict(zip(cols, row))["user_id"]): dict(zip(cols, row))
                        for row in rows
                    }
        finally:
            await release_db_connection(conn)

    async def _dest_for_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = channel.get("brand_id")
        target_ids = channel.get("publish_targets") or []
        if not brand_id or not target_ids:
            return {}
        resolved = await resolve_publish_targets(int(brand_id), target_ids)
        return publish_targets_to_destination_fields(resolved)

    async def _persist_session_cookies(self, user_id: int, cookies_json: Optional[str]) -> None:
        if cookies_json is None:
            return
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE threads_profiles SET
                        session_cookies = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (cookies_json, user_id),
                )
        except Exception as exc:
            logger.debug("persist session_cookies failed: %s", exc)
        finally:
            await release_db_connection(conn)

    async def _native_id_exists(self, user_id: int, native_id: str) -> bool:
        nid = (native_id or "").strip()
        if not nid:
            return False
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 1 FROM posts
                    WHERE user_id = %s AND source_platform = 'threads'
                      AND source_native_id = %s
                    LIMIT 1
                    """,
                    (user_id, nid),
                )
                return await cur.fetchone() is not None
        finally:
            await release_db_connection(conn)

    async def _recent_known_ids(self, user_id: int, limit: int = 300) -> Set[str]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT source_native_id FROM posts
                    WHERE user_id = %s AND source_platform = 'threads'
                      AND source_native_id IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)
        known: Set[str] = set()
        for row in rows:
            raw = str(row[0] or "")
            pid = extract_post_id(raw) or raw.rsplit("/", 1)[-1]
            if pid:
                known.add(pid)
            known.add(raw)
        return known

    async def _insert_collected(
        self,
        user_id: int,
        text: str,
        url: str,
        *,
        screenshot: Optional[str] = None,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        domain: Optional[str] = None,
        author: Optional[str] = None,
        native_id: Optional[str] = None,
    ) -> Optional[int]:
        dest = dest or {}
        platforms = dest_flags_to_platforms(dest)
        if not platforms:
            platforms = ("threads",)
        nid = (native_id or url or "").strip()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                created = await PostsRepository(cur).create_inbound(
                    InboundPostCreate(
                        user_id=user_id,
                        source_platform="threads",
                        post_text=text,
                        url=url,
                        screenshot=screenshot,
                        brand_id=brand_id,
                        channel_id=channel_id,
                        domain=domain,
                        author=author,
                        extras={"thread_url": url},
                        source_native_id=nid,
                        target_channels=dest.get("target_channels") or [],
                        target_groups=dest.get("target_groups") or [],
                        target_platforms=platforms,
                        target_status="pending",
                    )
                )
                post_row_id = int(created["id"])
            await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
            return post_row_id
        finally:
            await release_db_connection(conn)

    async def _save_if_new(
        self,
        user_id: int,
        post_id: str,
        text: str,
        url: str,
        *,
        screenshot: Optional[str] = None,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        domain: Optional[str] = None,
        author: Optional[str] = None,
        save_conditions: Optional[List[str]] = None,
        conditions_mode: str = "any_of",
    ) -> bool:
        tid = (post_id or "").strip()
        if not tid:
            return False
        body = (text or "").strip()
        if not should_save_text(body, save_conditions or [], conditions_mode or "any_of"):
            return False
        native = url or tid
        if await self._native_id_exists(user_id, native):
            return False
        if await self._native_id_exists(user_id, tid):
            return False
        row_id = await self._insert_collected(
            user_id,
            body,
            url or native,
            screenshot=screenshot,
            dest=dest,
            brand_id=brand_id,
            channel_id=channel_id,
            domain=domain,
            author=author,
            native_id=native,
        )
        if row_id is None:
            return False
        if channel_id is not None or domain:
            await bump_channel_counter(
                user_id,
                network="threads",
                external_id=domain or "",
                channel_id=channel_id,
                received=1,
                direction="collected",
                platform="threads",
                post_id=row_id,
                external_msg_id=tid,
                metadata={"text_preview": body[:120]},
            )
        _log_action(
            "Collected threads post %s user=%s brand=%s channel=%s",
            tid,
            user_id,
            brand_id,
            channel_id,
        )
        return True

    async def collect_channel_browser(
        self,
        pr: Dict[str, Any],
        handle: str,
        *,
        dest: Dict[str, Any],
        brand_id: Optional[int],
        channel_id: Optional[int],
        save_conditions: List[str],
        conditions_mode: str,
    ) -> int:
        user_id = int(pr["user_id"])
        login, password = _browser_creds(pr)
        if not login or not password:
            return 0
        known = await self._recent_known_ids(user_id)
        take_shot = bool(pr.get("take_screenshot_collect"))
        result = await collect_user_timeline_for_profile(
            login=login,
            password=password,
            cookies_json=pr.get("session_cookies"),
            take_screenshot=take_shot,
            known_post_ids=known,
            user_id=user_id,
            handle=handle,
        )
        if result.cookies_json:
            await self._persist_session_cookies(user_id, result.cookies_json)
        if not result.ok:
            if result.diag_png:
                await upload_selenium_diagnostic_png(user_id, 0, result.diag_png)
            logger.warning(
                "Browser threads collect user=%s @%s failed: %s",
                user_id,
                handle,
                (result.error or "unknown")[:500],
            )
            return 0
        saved = 0
        for post in result.posts:
            ok = await self._save_if_new(
                user_id,
                post.post_id,
                post.text,
                post.url,
                screenshot=post.screenshot_path if take_shot else None,
                dest=dest,
                brand_id=brand_id,
                channel_id=channel_id,
                domain=handle,
                author=handle,
                save_conditions=save_conditions,
                conditions_mode=conditions_mode,
            )
            if ok:
                saved += 1
        return saved

    async def collect_channel_api(
        self,
        pr: Dict[str, Any],
        handle: str,
        *,
        dest: Dict[str, Any],
        brand_id: Optional[int],
        channel_id: Optional[int],
        save_conditions: List[str],
        conditions_mode: str,
    ) -> int:
        user_id = int(pr["user_id"])
        token = (pr.get("access_token") or "").strip()
        if not token:
            return 0

        threads_uid = str(pr.get("threads_user_id") or "").strip()
        own = _own_handle(pr).lower()
        target = handle.lower()
        is_own = (own and own == target) or (
            threads_uid and (threads_uid == handle or (handle.isdigit() and threads_uid == handle))
        )

        api_uid = threads_uid if is_own else ""
        if not api_uid and not is_own:
            looked = await lookup_profile_by_username(token, handle)
            if looked and looked.get("id"):
                api_uid = str(looked["id"])
        if not api_uid:
            # Only own timeline is reliably available on many Meta app configs.
            if is_own and threads_uid:
                api_uid = threads_uid
            else:
                return 0

        tweets = await fetch_user_threads(token, api_uid)
        saved = 0
        for item in tweets:
            tid = str(item.get("id") or "").strip()
            text = (item.get("text") or "").strip()
            permalink = item.get("permalink")
            url = canonical_thread_url(tid, permalink if isinstance(permalink, str) else None)
            if not tid:
                continue
            ok = await self._save_if_new(
                user_id,
                tid,
                text,
                url,
                dest=dest,
                brand_id=brand_id,
                channel_id=channel_id,
                domain=handle,
                author=(item.get("username") or handle),
                save_conditions=save_conditions,
                conditions_mode=conditions_mode,
            )
            if ok:
                saved += 1
        return saved

    async def collect_own_legacy(self, pr: Dict[str, Any]) -> int:
        """Legacy: collect_enabled → свои посты через API."""
        if not pr.get("collect_enabled"):
            return 0
        token = (pr.get("access_token") or "").strip()
        uid = str(pr.get("threads_user_id") or "").strip()
        if not token or not uid:
            return 0
        handle = _own_handle(pr) or uid
        return await self.collect_channel_api(
            pr,
            handle,
            dest={},
            brand_id=None,
            channel_id=None,
            save_conditions=[],
            conditions_mode="any_of",
        )

    async def run_collect(self) -> int:
        profiles = await self._profiles_map()
        if not profiles:
            return 0

        total = 0
        polled: Set[Tuple[int, str]] = set()

        channels = await list_threads_flow_channels()
        for channel in channels:
            user_id = int(channel["user_id"])
            pr = profiles.get(user_id)
            if not pr:
                logger.debug(
                    "Skip Threads brand channel %s: no oauth/browser creds for user=%s",
                    channel.get("id"),
                    user_id,
                )
                continue
            handle = normalize_threads_handle(str(channel.get("external_id") or ""))
            if not handle:
                logger.warning(
                    "Skip Threads brand channel %s: bad external_id=%r",
                    channel.get("id"),
                    channel.get("external_id"),
                )
                continue
            key = (user_id, handle.lower())
            if key in polled:
                continue

            dest = await self._dest_for_channel(channel)
            brand_id = (
                int(channel["brand_id"]) if channel.get("brand_id") is not None else None
            )
            channel_id = int(channel["id"]) if channel.get("id") is not None else None
            kwargs = {
                "dest": dest,
                "brand_id": brand_id,
                "channel_id": channel_id,
                "save_conditions": channel.get("save_conditions") or [],
                "conditions_mode": channel.get("conditions_mode") or "any_of",
            }

            n = 0
            if _has_browser_creds(pr):
                try:
                    n = await self.collect_channel_browser(pr, handle, **kwargs)
                except Exception as exc:
                    logger.exception(
                        "collect_channel_browser user=%s @%s: %s", user_id, handle, exc
                    )
            if n == 0 and _has_oauth(pr):
                try:
                    n = await self.collect_channel_api(pr, handle, **kwargs)
                except Exception as exc:
                    logger.exception(
                        "collect_channel_api user=%s @%s: %s", user_id, handle, exc
                    )
            total += n
            polled.add(key)

        for user_id, pr in profiles.items():
            try:
                total += await self.collect_own_legacy(pr)
            except Exception as exc:
                logger.exception("collect_own_legacy user=%s: %s", user_id, exc)

        return total
