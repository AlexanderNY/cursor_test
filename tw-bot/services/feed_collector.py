"""Сбор твитов в posts для collect_enabled-профилей (API + браузерная лента Following)."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import httpx

from config import settings
from database import get_db_connection, release_db_connection
from shared.db.posts_repo import InboundPostCreate, PostsRepository
from shared.queue_wakeup import wake_process_http

from .x_client import ensure_user_access_token, fetch_timeline_tweets
from .x_feed_browser import (
    canonical_status_url,
    collect_following_feed_for_profile,
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
    """Вызывает url-bot POST /run (как c-url) — только для API-сбора без cookies."""
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
    """Вставляет твиты из API и браузерной ленты Following (status=collected)."""

    async def _profiles_to_collect_api(self) -> List[Dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, twitter_rest_id, twitter_oauth_access_token,
                           twitter_oauth_refresh_token, twitter_oauth_expires_at,
                           take_screenshot_collect, screenshot_xpath
                    FROM tw_profiles
                    WHERE collect_enabled = TRUE
                      AND twitter_rest_id IS NOT NULL
                      AND twitter_rest_id != ''
                      AND twitter_oauth_refresh_token IS NOT NULL
                      AND twitter_oauth_refresh_token != ''
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        finally:
            await release_db_connection(conn)

    async def _profiles_to_collect_browser(self) -> List[Dict[str, Any]]:
        """Профили с паролем X — чтение UI-ленты Following."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, twitter_username, twitter_password,
                           twitter_session_cookies, take_screenshot_collect,
                           use_proxy, proxy_host, proxy_port, proxy_user, proxy_pass
                    FROM tw_profiles
                    WHERE collect_enabled = TRUE
                      AND twitter_password IS NOT NULL
                      AND twitter_password != ''
                      AND twitter_username IS NOT NULL
                      AND twitter_username != ''
                    """
                )
                rows = await cur.fetchall()
                cols = [c.name for c in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        finally:
            await release_db_connection(conn)

    async def _insert_collected(
        self,
        user_id: int,
        text: str,
        url: str,
        screenshot: Optional[str],
    ) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await PostsRepository(cur).create_inbound(
                    InboundPostCreate(
                        user_id=user_id,
                        source_platform="tw",
                        post_text=text,
                        url=url,
                        screenshot=screenshot,
                        extras={"tweet_url": url},
                        source_native_id=url,
                        target_platforms=("tw",),
                        target_status="pending",
                    )
                )
            await wake_process_http(getattr(settings, "PROCESSOR_SERVICE_URL", "") or "")
        finally:
            await release_db_connection(conn)

    async def collect_for_profile(self, pr: Dict[str, Any]) -> int:
        """OAuth API: reverse chronological или свои твиты пользователя."""
        user_id = pr["user_id"]
        rest_id = str(pr["twitter_rest_id"] or "").strip()
        if not rest_id:
            return 0

        acc, ref, exp = await ensure_user_access_token(
            pr.get("twitter_oauth_access_token"),
            pr.get("twitter_oauth_refresh_token"),
            pr.get("twitter_oauth_expires_at"),
        )
        if not acc:
            logger.warning("Feed collect user_id=%s: no access token", user_id)
            return 0

        if acc != pr.get("twitter_oauth_access_token"):
            await self._persist_tokens(user_id, acc, ref, exp)

        tweets = await fetch_timeline_tweets(acc, rest_id)
        saved = 0
        xpath_default = (pr.get("screenshot_xpath") or "").strip() or settings.DEFAULT_TWEET_SCREENSHOT_XPATH
        take_shot = bool(pr.get("take_screenshot_collect"))

        for tw in tweets:
            tid = str(tw.get("id") or "")
            text = (tw.get("text") or "").strip()
            if not tid:
                continue
            url = canonical_status_url(tid)
            if await _status_id_exists(user_id, tid):
                continue

            screenshot_path = None
            if take_shot:
                screenshot_path = await _screenshot_tweet(user_id, url, xpath_default)

            await self._insert_collected(user_id, text, url, screenshot_path)
            saved += 1
            _log_action("Collected tweet %s for user_id=%s", tid, user_id)

        return saved

    async def collect_browser_for_profile(self, pr: Dict[str, Any]) -> int:
        """Selenium: домашняя лента Following + скрин карточки в той же сессии."""
        user_id = int(pr["user_id"])
        username_raw = (pr.get("twitter_username") or "").strip()
        password = (pr.get("twitter_password") or "").strip()
        if isinstance(password, str):
            password = password.strip()
        else:
            password = ""
        if not username_raw or not password:
            return 0

        login, _handle = normalize_login_handle(username_raw)
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

        known = await _recent_known_status_ids(user_id)
        take_shot = bool(pr.get("take_screenshot_collect"))
        result = await collect_following_feed_for_profile(
            login=login,
            password=password,
            cookies_json=pr.get("twitter_session_cookies"),
            proxy=proxy,
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
            if await _status_id_exists(user_id, tweet.status_id):
                continue
            shot_path = tweet.screenshot_path if take_shot else None
            await self._insert_collected(user_id, tweet.text, tweet.url, shot_path)
            saved += 1
            _log_action(
                "Browser collected tweet %s for user_id=%s",
                tweet.status_id,
                user_id,
            )
        return saved

    async def run_collect(self) -> int:
        total = 0
        for pr in await self._profiles_to_collect_api():
            try:
                total += await self.collect_for_profile(pr)
            except Exception as e:
                logger.exception("collect_for_profile user_id=%s: %s", pr.get("user_id"), e)

        for pr in await self._profiles_to_collect_browser():
            try:
                total += await self.collect_browser_for_profile(pr)
            except Exception as e:
                logger.exception(
                    "collect_browser_for_profile user_id=%s: %s",
                    pr.get("user_id"),
                    e,
                )
        return total
