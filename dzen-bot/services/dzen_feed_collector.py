"""Сбор ссылок на публикации со страницы студии Дзен (Selenium)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from selenium.webdriver.common.by import By

from config import settings
from database import get_db_connection, release_db_connection

from .selenium_diag import capture_selenium_error_to_s3
from .selenium_driver import create_chrome_driver
from .selenium_errors import format_selenium_exception
from .yandex_auth import YandexAuthError
from .yandex_dzen_flow import yandex_auth_dispatch

logger = logging.getLogger(__name__)


async def _fetch_collect_profiles() -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT user_id, yandex_login, yandex_password, dzen_studio_url, COALESCE(collect_source, 'rss') AS collect_source
                FROM dzen_profiles
                WHERE collect_enabled = TRUE
                  AND dzen_studio_url IS NOT NULL
                  AND TRIM(dzen_studio_url) <> ''
                  AND yandex_login IS NOT NULL
                  AND TRIM(yandex_login) <> ''
                  AND yandex_password IS NOT NULL
                  AND TRIM(yandex_password) <> ''
                  AND COALESCE(collect_source, 'rss') IN ('selenium', 'both')
                """
            )
            rows = await cur.fetchall()
            cols = ["user_id", "yandex_login", "yandex_password", "dzen_studio_url", "collect_source"]
            return [dict(zip(cols, row)) for row in rows]
    finally:
        await release_db_connection(conn)


async def _set_last_auth_error(user_id: int, message: Optional[str]) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE dzen_profiles SET last_auth_error = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (message, user_id),
            )
    finally:
        await release_db_connection(conn)


async def _insert_item(user_id: int, item: Dict[str, Any]) -> int:
    link = (item.get("link") or "").strip()
    if not link:
        return 0
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM dzen_posts WHERE user_id = %s AND url = %s LIMIT 1",
                (user_id, link),
            )
            if await cur.fetchone():
                return 0
            images_json = json.dumps(item.get("images") or [], ensure_ascii=False)
            await cur.execute(
                """
                INSERT INTO dzen_posts (
                    user_id, url, title, post_date, post_text, images,
                    status, post_type, to_dzen
                ) VALUES (%s, %s, %s, %s, %s, %s, 'collected', 'dzen_selenium', TRUE)
                """,
                (
                    user_id,
                    link,
                    (item.get("title") or "")[:500],
                    None,
                    (item.get("post_text") or "")[:150000],
                    images_json,
                ),
            )
            return 1
    finally:
        await release_db_connection(conn)


def _collect_links_sync(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    login = (profile.get("yandex_login") or "").strip()
    password = (profile.get("yandex_password") or "").strip()
    studio_url = (profile.get("dzen_studio_url") or "").strip()
    if not studio_url:
        return [], "Пустой dzen_studio_url"

    driver = None
    try:
        driver = create_chrome_driver()
        yandex_auth_dispatch(driver, login, password)
        driver.get(studio_url)
        time.sleep(3.5)

        normalized: set[str] = set()
        for _ in range(max(1, settings.DZEN_FEED_MAX_SCROLLS)):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(settings.DZEN_FEED_SCROLL_PAUSE_SEC)
            try:
                anchors = driver.find_elements(By.CSS_SELECTOR, settings.DZEN_FEED_ITEM_LINK_SELECTOR)
            except Exception:
                anchors = []
            for a in anchors:
                href = (a.get_attribute("href") or "").strip()
                if not href or "/article/" not in href:
                    continue
                key = href.split("?")[0].split("#")[0]
                normalized.add(key)

        items: List[Dict[str, Any]] = [
            {"link": link, "title": "", "post_text": "", "images": []} for link in sorted(normalized)
        ]
        return items, None
    except YandexAuthError as e:
        uid = profile.get("user_id")
        capture_selenium_error_to_s3(driver, "feed_collect_yandex_auth", user_id=uid)
        return [], str(e)
    except Exception as e:
        uid = profile.get("user_id")
        capture_selenium_error_to_s3(driver, "feed_collect_exception", user_id=uid)
        logger.exception("Dzen feed collect: %s", e)
        return [], format_selenium_exception(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


class DzenFeedCollector:
    """Вставляет новые ссылки из студии в dzen_posts (collected)."""

    async def run_collect(self) -> int:
        profiles = await _fetch_collect_profiles()
        if not profiles:
            return 0
        total = 0
        for prof in profiles:
            uid = prof["user_id"]
            await _set_last_auth_error(uid, None)
            items, err = await asyncio.to_thread(_collect_links_sync, prof)
            if err:
                await _set_last_auth_error(uid, err[:2000])
                logger.warning("Dzen collect user %s: %s", uid, err)
                continue
            for it in items:
                try:
                    total += await _insert_item(uid, it)
                except Exception as e:
                    logger.exception("Dzen insert user %s: %s", uid, e)
        return total
