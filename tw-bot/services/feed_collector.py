"""
Сбор твитов в posts.

Приоритет:
1) Brand channels (network=tw, collect_enabled) — таймлайн @handle
   - браузер x.com/{handle} (основной путь; Free API часто недоступен)
   - fallback: OAuth API users/by/username + users/:id/tweets
2) Legacy: tw_profiles.collect_enabled → API home/own + Selenium Following
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from config import settings
from database import get_db_connection, release_db_connection
from shared.db.bot_queue import dest_flags_to_platforms
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http
from shared.text_conditions import should_save_text

from .brand_channel_flow import (
    list_tw_flow_channels,
    normalize_tw_handle,
    publish_targets_to_destination_fields,
    resolve_publish_targets,
)
from .channel_counter import bump_channel_counter
from .x_client import (
    ensure_user_access_token,
    fetch_timeline_tweets,
    fetch_user_tweets,
    lookup_user_by_username,
)
from .x_feed_browser import (
    canonical_status_url,
    collect_following_feed_for_profile,
    collect_user_timeline_for_profile,
    extract_status_id,
    normalize_login_handle,
)
from .x_selenium_verify import _upload_diag_screenshot

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _proxy_from_profile(pr: Dict[str, Any]) -> Dict[str, Any]:
    use_proxy = bool(pr.get("use_proxy"))
    proxy_host = (pr.get("proxy_host") or "").strip() if pr.get("proxy_host") else ""
    proxy: Dict[str, Any] = {
        "use_proxy": use_proxy,
        "proxy_host": proxy_host,
        "proxy_port": pr.get("proxy_port"),
        "proxy_user": (pr.get("proxy_user") or "").strip() if pr.get("proxy_user") else "",
        "proxy_pass": (pr.get("proxy_pass") or "").strip() if pr.get("proxy_pass") else "",
    }
    if use_proxy and proxy_host:
        proxy["host"] = proxy_host
        port = pr.get("proxy_port")
        proxy["port"] = int(port) if port is not None else 80
    return proxy


def _has_browser_creds(pr: Dict[str, Any]) -> bool:
    user = (pr.get("twitter_username") or "").strip()
    password = pr.get("twitter_password")
    if isinstance(password, str):
        password = password.strip()
    else:
        password = ""
    return bool(user and password)


def _has_oauth(pr: Dict[str, Any]) -> bool:
    return bool((pr.get("twitter_oauth_refresh_token") or "").strip())


async def _persist_tokens(
    user_id: int,
    access_token: str,
    refresh_token: Optional[str],
    expires_at: Optional[datetime],
) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE tw_profiles SET
                    twitter_oauth_access_token = %s,
                    twitter_oauth_refresh_token = COALESCE(%s, twitter_oauth_refresh_token),
                    twitter_oauth_expires_at = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (access_token, refresh_token, expires_at, user_id),
            )
    finally:
        await release_db_connection(conn)


async def _persist_session_cookies(user_id: int, cookies_json: Optional[str]) -> None:
    if cookies_json is None:
        return
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE tw_profiles SET
                    twitter_session_cookies = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (cookies_json, user_id),
            )
    finally:
        await release_db_connection(conn)


async def _status_id_exists(user_id: int, status_id: str) -> bool:
    """True если пост с этим status id уже есть (любой канонический/сырой URL)."""
    tid = (status_id or "").strip()
    if not tid:
        return False
    canonical = canonical_status_url(tid)
    like_pat = f"%/status/{tid}"
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT 1 FROM posts
                WHERE user_id = %s
                  AND source_platform = 'tw'
                  AND (
                    source_native_id = %s
                    OR source_native_id LIKE %s
                  )
                LIMIT 1
                """,
                (user_id, canonical, like_pat),
            )
            row = await cur.fetchone()
            return row is not None
    finally:
        await release_db_connection(conn)


async def _recent_known_status_ids(user_id: int, limit: int = 300) -> Set[str]:
    """Недавние status id пользователя — для ранней остановки скролла ленты."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT source_native_id FROM posts
                WHERE user_id = %s AND source_platform = 'tw'
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
        sid = extract_status_id(str(row[0] or ""))
        if sid:
            known.add(sid)
    return known


async def _screenshot_tweet(
    user_id: int,
    tweet_url: str,
    xpath: str,
) -> Optional[str]:
    """Вызывает url-bot POST /run — только для API-сбора без cookies."""
    base = settings.URL_BOT_SERVICE_URL.rstrip("/")
    payload = {
        "url": tweet_url,
        "xpath": xpath,
        "take_screenshot": True,
        "user_id": user_id,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base}/run", json=payload)
            data = resp.json()
            if resp.status_code >= 400:
                logger.warning("url-bot screenshot failed: %s", data)
                return None
            return data.get("screenshot_path") or None
    except Exception as e:
        logger.warning("url-bot screenshot: %s", e)
        return None


class FeedCollector:
    """Brand-channel timelines + legacy profile Following/API."""

    async def _profiles_map(self) -> Dict[int, Dict[str, Any]]:
        """user_id → tw_profiles (oauth and/or browser creds)."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, twitter_rest_id, twitter_username, twitter_password,
                           twitter_oauth_access_token, twitter_oauth_refresh_token,
                           twitter_oauth_expires_at, twitter_session_cookies,
                           collect_enabled, take_screenshot_collect, screenshot_xpath,
                           use_proxy, proxy_host, proxy_port, proxy_user, proxy_pass
                    FROM tw_profiles
                    WHERE (
                        (twitter_oauth_refresh_token IS NOT NULL AND twitter_oauth_refresh_token != '')
                        OR (
                            twitter_password IS NOT NULL AND twitter_password != ''
                            AND twitter_username IS NOT NULL AND twitter_username != ''
                        )
                    )
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                return {int(dict(zip(cols, row))["user_id"]): dict(zip(cols, row)) for row in rows}
        finally:
            await release_db_connection(conn)

    async def _dest_for_channel(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = channel.get("brand_id")
        target_ids = channel.get("publish_targets") or []
        if not brand_id or not target_ids:
            return {}
        resolved = await resolve_publish_targets(int(brand_id), target_ids)
        return publish_targets_to_destination_fields(resolved)

    async def _insert_collected(
        self,
        user_id: int,
        text: str,
        url: str,
        screenshot: Optional[str],
        *,
        dest: Optional[Dict[str, Any]] = None,
        brand_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        domain: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Optional[int]:
        dest = dest or {}
        platforms = dest_flags_to_platforms(dest)
        if not platforms:
            platforms = ("tw",)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                created = await PostsRepository(cur).create_inbound(
                    InboundPostCreate(
                        user_id=user_id,
                        source_platform="tw",
                        post_text=text,
                        url=url,
                        screenshot=screenshot,
                        brand_id=brand_id,
                        channel_id=channel_id,
                        domain=domain,
                        author=author,
                        extras={"tweet_url": url},
                        source_native_id=url,
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

    async def _save_tweet_if_new(
        self,
        user_id: int,
        status_id: str,
        text: str,
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
        tid = (status_id or "").strip()
        if not tid:
            return False
        body = (text or "").strip()
        if not should_save_text(body, save_conditions or [], conditions_mode or "any_of"):
            return False
        if await _status_id_exists(user_id, tid):
            return False
        url = canonical_status_url(tid)
        post_id = await self._insert_collected(
            user_id,
            body,
            url,
            screenshot,
            dest=dest,
            brand_id=brand_id,
            channel_id=channel_id,
            domain=domain,
            author=author,
        )
        if post_id is None:
            return False
        if channel_id is not None or domain:
            await bump_channel_counter(
                user_id,
                network="tw",
                external_id=domain or "",
                channel_id=channel_id,
                received=1,
                direction="collected",
                platform="tw",
                post_id=post_id,
                external_msg_id=tid,
                metadata={"text_preview": body[:120]},
            )
        _log_action(
            "Collected tweet %s user=%s brand=%s channel=%s",
            tid,
            user_id,
            brand_id,
            channel_id,
        )
        return True

    async def _ensure_access(self, pr: Dict[str, Any]) -> Optional[str]:
        acc, ref, exp = await ensure_user_access_token(
            pr.get("twitter_oauth_access_token"),
            pr.get("twitter_oauth_refresh_token"),
            pr.get("twitter_oauth_expires_at"),
        )
        if not acc:
            return None
        if acc != pr.get("twitter_oauth_access_token"):
            await _persist_tokens(int(pr["user_id"]), acc, ref, exp)
            pr["twitter_oauth_access_token"] = acc
            pr["twitter_oauth_refresh_token"] = ref
            pr["twitter_oauth_expires_at"] = exp
        return acc

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
        username_raw = (pr.get("twitter_username") or "").strip()
        password = (pr.get("twitter_password") or "").strip()
        if not username_raw or not password:
            return 0
        login, _ = normalize_login_handle(username_raw)
        known = await _recent_known_status_ids(user_id)
        take_shot = bool(pr.get("take_screenshot_collect"))
        result = await collect_user_timeline_for_profile(
            login=login,
            password=password,
            cookies_json=pr.get("twitter_session_cookies"),
            proxy=_proxy_from_profile(pr),
            take_screenshot=take_shot,
            known_status_ids=known,
            user_id=user_id,
            handle=handle,
        )
        if result.cookies_json:
            await _persist_session_cookies(user_id, result.cookies_json)
        if not result.ok:
            if result.diag_png:
                await _upload_diag_screenshot(user_id, result.diag_png)
            logger.warning(
                "Browser channel collect user=%s @%s failed: %s",
                user_id,
                handle,
                (result.error or "unknown")[:500],
            )
            return 0
        saved = 0
        for tweet in result.tweets:
            ok = await self._save_tweet_if_new(
                user_id,
                tweet.status_id,
                tweet.text,
                screenshot=tweet.screenshot_path if take_shot else None,
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
        acc = await self._ensure_access(pr)
        if not acc:
            return 0
        rest_id = handle if handle.isdigit() else None
        if not rest_id:
            looked = await lookup_user_by_username(acc, handle)
            if not looked or not looked.get("id"):
                logger.debug("API lookup failed for @%s user=%s", handle, user_id)
                return 0
            rest_id = str(looked["id"])
        tweets = await fetch_user_tweets(acc, rest_id)
        xpath_default = (
            (pr.get("screenshot_xpath") or "").strip() or settings.DEFAULT_TWEET_SCREENSHOT_XPATH
        )
        take_shot = bool(pr.get("take_screenshot_collect"))
        saved = 0
        for tw in tweets:
            tid = str(tw.get("id") or "")
            text = (tw.get("text") or "").strip()
            if not tid:
                continue
            shot = None
            if take_shot:
                shot = await _screenshot_tweet(user_id, canonical_status_url(tid), xpath_default)
            ok = await self._save_tweet_if_new(
                user_id,
                tid,
                text,
                screenshot=shot,
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

    async def collect_for_profile(self, pr: Dict[str, Any]) -> int:
        """OAuth API: reverse chronological или свои твиты пользователя (legacy)."""
        user_id = pr["user_id"]
        rest_id = str(pr.get("twitter_rest_id") or "").strip()
        if not rest_id:
            return 0
        acc = await self._ensure_access(pr)
        if not acc:
            logger.warning("Feed collect user_id=%s: no access token", user_id)
            return 0
        tweets = await fetch_timeline_tweets(acc, rest_id)
        xpath_default = (
            (pr.get("screenshot_xpath") or "").strip() or settings.DEFAULT_TWEET_SCREENSHOT_XPATH
        )
        take_shot = bool(pr.get("take_screenshot_collect"))
        saved = 0
        for tw in tweets:
            tid = str(tw.get("id") or "")
            text = (tw.get("text") or "").strip()
            if not tid:
                continue
            shot = None
            if take_shot:
                shot = await _screenshot_tweet(user_id, canonical_status_url(tid), xpath_default)
            if await self._save_tweet_if_new(user_id, tid, text, screenshot=shot):
                saved += 1
        return saved

    async def collect_browser_for_profile(self, pr: Dict[str, Any]) -> int:
        """Selenium: домашняя лента Following (legacy profile collect)."""
        user_id = int(pr["user_id"])
        username_raw = (pr.get("twitter_username") or "").strip()
        password = (pr.get("twitter_password") or "").strip()
        if not username_raw or not password:
            return 0
        login, _handle = normalize_login_handle(username_raw)
        known = await _recent_known_status_ids(user_id)
        take_shot = bool(pr.get("take_screenshot_collect"))
        result = await collect_following_feed_for_profile(
            login=login,
            password=password,
            cookies_json=pr.get("twitter_session_cookies"),
            proxy=_proxy_from_profile(pr),
            take_screenshot=take_shot,
            known_status_ids=known,
            user_id=user_id,
        )
        if result.cookies_json:
            await _persist_session_cookies(user_id, result.cookies_json)
        if not result.ok:
            if result.diag_png:
                await _upload_diag_screenshot(user_id, result.diag_png)
            logger.warning(
                "Browser feed collect user_id=%s failed: %s",
                user_id,
                (result.error or "unknown")[:500],
            )
            return 0
        saved = 0
        for tweet in result.tweets:
            if await self._save_tweet_if_new(
                user_id,
                tweet.status_id,
                tweet.text,
                screenshot=tweet.screenshot_path if take_shot else None,
            ):
                saved += 1
        return saved

    async def run_collect(self) -> int:
        profiles = await self._profiles_map()
        if not profiles:
            return 0

        total = 0
        polled: Set[Tuple[int, str]] = set()  # (user_id, handle_lower)

        channels = await list_tw_flow_channels()
        for channel in channels:
            user_id = int(channel["user_id"])
            pr = profiles.get(user_id)
            if not pr:
                logger.debug(
                    "Skip TW brand channel %s: no tw_profiles oauth/browser creds for user=%s",
                    channel.get("id"),
                    user_id,
                )
                continue
            handle = normalize_tw_handle(str(channel.get("external_id") or ""))
            if not handle:
                logger.warning(
                    "Skip TW brand channel %s: bad external_id=%r",
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
            save_conditions = channel.get("save_conditions") or []
            conditions_mode = channel.get("conditions_mode") or "any_of"
            kwargs = {
                "dest": dest,
                "brand_id": brand_id,
                "channel_id": channel_id,
                "save_conditions": save_conditions,
                "conditions_mode": conditions_mode,
            }

            n = 0
            # Browser first — reliable for arbitrary handles on Free/Basic API plans.
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
            if n == 0 and not _has_browser_creds(pr) and not _has_oauth(pr):
                logger.debug(
                    "Skip TW channel @%s user=%s: need OAuth or X login/password",
                    handle,
                    user_id,
                )
            total += n
            polled.add(key)

        # Legacy profile-level Following / API home
        for user_id, pr in profiles.items():
            if not pr.get("collect_enabled"):
                continue
            try:
                if _has_oauth(pr) and str(pr.get("twitter_rest_id") or "").strip():
                    total += await self.collect_for_profile(pr)
            except Exception as e:
                logger.exception("collect_for_profile user_id=%s: %s", user_id, e)
            try:
                if _has_browser_creds(pr):
                    total += await self.collect_browser_for_profile(pr)
            except Exception as e:
                logger.exception("collect_browser_for_profile user_id=%s: %s", user_id, e)

        return total
