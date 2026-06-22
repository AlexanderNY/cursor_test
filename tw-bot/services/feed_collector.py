"""Сбор твитов в tw_posts для collect_enabled-профилей."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from config import settings
from database import get_db_connection, release_db_connection

from .x_client import ensure_user_access_token, fetch_timeline_tweets

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


async def _url_exists(user_id: int, url: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM tw_posts WHERE user_id = %s AND url = %s LIMIT 1",
                (user_id, url),
            )
            row = await cur.fetchone()
            return row is not None
    finally:
        await release_db_connection(conn)


async def _screenshot_tweet(
    user_id: int,
    tweet_url: str,
    xpath: str,
) -> Optional[str]:
    """Вызывает url-bot POST /run (как c-url)."""
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
    """Вставляет твиты из API в tw_posts (status=collected)."""

    async def _profiles_to_collect(self) -> List[Dict[str, Any]]:
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
                await cur.execute(
                    """
                    INSERT INTO tw_posts (
                        user_id, post_text, url, status, post_type, screenshot,
                        to_tg, to_tw, to_wp, to_vk
                    ) VALUES (
                        %s, %s, %s, 'collected', 'tw', %s,
                        FALSE, FALSE, FALSE, FALSE
                    )
                    """,
                    (user_id, text, url, screenshot),
                )
        finally:
            await release_db_connection(conn)

    async def collect_for_profile(self, pr: Dict[str, Any]) -> int:
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
            url = f"https://x.com/i/web/status/{tid}"
            if await _url_exists(user_id, url):
                continue

            screenshot_path = None
            if take_shot:
                screenshot_path = await _screenshot_tweet(user_id, url, xpath_default)

            await self._insert_collected(user_id, text, url, screenshot_path)
            saved += 1
            _log_action("Collected tweet %s for user_id=%s", tid, user_id)

        return saved

    async def run_collect(self) -> int:
        profiles = await self._profiles_to_collect()
        total = 0
        for pr in profiles:
            try:
                total += await self.collect_for_profile(pr)
            except Exception as e:
                logger.exception("collect_for_profile user_id=%s: %s", pr.get("user_id"), e)
        return total
