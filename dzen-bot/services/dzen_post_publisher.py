"""Публикация постов dzen_posts (status=ready) в интерфейс Дзена через Selenium."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

import httpx
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from database import get_db_connection, release_db_connection
from storage_helper import get_storage
from shared import async_fs
from shared.db.bot_queue import claimed_target_as_post, finish_claimed_publish
from shared.db.posts_repo import PostsRepository

from .selenium_diag import capture_selenium_error_to_s3
from .selenium_driver import create_chrome_driver, get_selenium_semaphore
from .selenium_errors import format_selenium_exception
from .yandex_auth import YandexAuthError, ensure_dzen_session
from .yandex_dzen_flow import yandex_auth_dispatch

logger = logging.getLogger(__name__)


def _log_action(msg: str, *args, **kwargs) -> None:
    if settings.LOG_BOT_ACTIONS:
        logger.info(msg, *args, **kwargs)
    else:
        logger.debug(msg, *args, **kwargs)


def _parse_images(raw: Any) -> List[str]:
    if raw is None:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    out: List[str] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            p = item.get("path") or item.get("url") or ""
            if p:
                out.append(str(p).strip())
    return out


def _resolve_path_local(path_or_url: str, base_dir: str) -> Optional[str]:
    if not path_or_url or not isinstance(path_or_url, str):
        return None
    s = path_or_url.strip()
    if s.lower().startswith(("http://", "https://")):
        return None
    if os.path.isabs(s) and os.path.isfile(s):
        return os.path.abspath(s)
    path = s.lstrip("/")
    base = (base_dir or os.getcwd()).rstrip("/")
    full = os.path.join(base, path)
    if os.path.isfile(full):
        return os.path.abspath(full)
    return None


def _resolve_image_url(path_or_url: str) -> str:
    s = (path_or_url or "").strip()
    if not s:
        return ""
    if s.lower().startswith(("http://", "https://")):
        return s
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return s
    return f"{base}{s}" if s.startswith("/") else f"{base}/{s}"


async def _download_to_temp(url: str, suffix: str = ".jpg") -> Optional[str]:
    if not url or not url.strip().lower().startswith(("http://", "https://")):
        return None
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return await async_fs.write_temp_bytes(resp.content, suffix=suffix)
    except Exception as e:
        logger.warning("Download failed %s: %s", url[:80], e)
        return None


async def _resolve_image_file(path_or_url: str, post_id: int) -> Optional[str]:
    s = (path_or_url or "").strip()
    if not s:
        return None
    if s.lower().startswith(("http://", "https://")):
        return await _download_to_temp(s)

    storage = get_storage()
    if storage:
        key = s.lstrip("/")
        if key:
            try:
                body = await storage.get_bytes(key)
                if body:
                    ext = os.path.splitext(key)[1] or ".jpg"
                    return await async_fs.write_temp_bytes(body, suffix=ext)
            except Exception as exc:
                logger.warning("Post %s: S3 get_bytes error: %s", post_id, exc)

    url = _resolve_image_url(s)
    if url.lower().startswith(("http://", "https://")):
        got = await _download_to_temp(url)
        if got:
            return got

    base = (settings.UPLOADS_DIR or os.getcwd()).rstrip("/")
    local = _resolve_path_local(s, base)
    if local:
        return local
    return None


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


async def _update_post_result(
    post: Dict[str, Any],
    status: str,
    url: Optional[str] = None,
) -> None:
    post_id = int(post["id"])
    user_id = int(post["user_id"])
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            finished = await finish_claimed_publish(
                cur,
                post,
                ok=(status == "published"),
                result={"url": url} if url else ({"error": "dzen publish failed"} if status == "failed" else {}),
                status=status,
            )
    finally:
        await release_db_connection(conn)
    from shared.bot_internal import mark_post_published

    if status == "published":
        await mark_post_published(
            settings.CORE_SERVICE_URL or "",
            platform="dzen",
            post_id=post_id,
            external_id=url,
        )
    elif status == "failed":
        await mark_post_published(
            settings.CORE_SERVICE_URL or "",
            platform="dzen",
            post_id=post_id,
            error="dzen publish failed",
        )


async def _fetch_ready_posts() -> List[Dict[str, Any]]:
    """Claim ready Dzen post_targets."""
    return await _claim_unified_dzen_posts()


async def _claim_unified_dzen_posts() -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            try:
                await cur.execute("BEGIN")
                rows = await PostsRepository(cur).claim_publish(platform="dzen", limit=5)
                await cur.execute("COMMIT")
            except Exception:
                await cur.execute("ROLLBACK")
                raise
        if not rows:
            return []
        claimed = [claimed_target_as_post(row) for row in rows]
        user_ids = sorted({int(p["user_id"]) for p in claimed})
        profiles = await _load_dzen_profiles(user_ids)
        for post in claimed:
            post.update(profiles.get(int(post["user_id"])) or {})
            post["status"] = "publishing"
        return claimed
    finally:
        await release_db_connection(conn)


async def _load_dzen_profiles(user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    if not user_ids:
        return {}
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            placeholders = ", ".join(["%s"] * len(user_ids))
            await cur.execute(
                f"""
                SELECT user_id, yandex_login, yandex_password, publish_enabled
                FROM dzen_profiles
                WHERE user_id IN ({placeholders})
                """,
                user_ids,
            )
            fetched = await cur.fetchall()
            cols = [c.name for c in cur.description]
            return {int(row[0]): dict(zip(cols, row)) for row in fetched}
    finally:
        await release_db_connection(conn)


def _find_editor_body(driver) -> Optional[Any]:
    selectors = [s.strip() for s in settings.DZEN_BODY_SELECTOR.split(",") if s.strip()]
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el and el.is_displayed():
                return el
        except Exception:
            continue
    try:
        els = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
        for el in els:
            if el.is_displayed():
                return el
    except Exception:
        pass
    return None


def _publish_sync(post: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Возвращает (ok, published_url, error_message).
    Пути к файлам изображений должны быть заранее в post['_local_image_paths'].
    """
    post_id = post.get("id")
    text = (post.get("post_text") or "")[:2000]
    title = (post.get("title") or "").strip()
    login = (post.get("yandex_login") or "").strip()
    password = (post.get("yandex_password") or "").strip()
    local_paths: List[str] = list(post.get("_local_image_paths") or [])

    driver = None
    temp_files: List[str] = list(local_paths)
    try:
        driver = create_chrome_driver()
        yandex_auth_dispatch(driver, login, password)
        ensure_dzen_session(driver)

        driver.get(settings.DZEN_NEW_ARTICLE_URL)
        time.sleep(4.0)

        wait = WebDriverWait(driver, 40)
        wait.until(lambda d: _find_editor_body(d) is not None)
        body_el = _find_editor_body(driver)
        if not body_el:
            return False, None, "Не найдено поле редактора статьи"

        if title:
            title_selectors = [s.strip() for s in settings.DZEN_TITLE_SELECTOR.split(",") if s.strip()]
            for tsel in title_selectors:
                try:
                    tel = driver.find_element(By.CSS_SELECTOR, tsel)
                    if tel and tel.is_displayed():
                        tel.clear()
                        tel.send_keys(title)
                        break
                except Exception:
                    continue

        try:
            body_el.click()
        except Exception:
            pass
        time.sleep(0.5)
        body_el.send_keys(text)

        for lp in local_paths:
            inputs = driver.find_elements(By.CSS_SELECTOR, settings.DZEN_FILE_INPUT_SELECTOR)
            if not inputs:
                break
            visible = [i for i in inputs if i.is_displayed()]
            use = visible[0] if visible else inputs[0]
            try:
                use.send_keys(lp)
                time.sleep(2.0)
            except Exception as ex:
                logger.warning("Post %s: file upload failed: %s", post_id, ex)

        time.sleep(1.0)
        pub_btn = WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable((By.XPATH, settings.DZEN_PUBLISH_BUTTON_XPATH))
        )
        pub_btn.click()
        time.sleep(6.0)
        final_url = (driver.current_url or "").strip()
        if "dzen.ru" in final_url and "/article/" in final_url:
            return True, final_url, None
        if "dzen.ru" in final_url:
            return True, final_url, None
        return False, None, "Публикация не подтверждена по URL страницы"
    except YandexAuthError as e:
        capture_selenium_error_to_s3(
            driver, "publish_post_yandex_auth", user_id=post.get("user_id")
        )
        return False, None, str(e)
    except Exception as e:
        capture_selenium_error_to_s3(
            driver, "publish_post_exception", user_id=post.get("user_id")
        )
        logger.exception("Dzen publish post %s: %s", post_id, e)
        return False, None, format_selenium_exception(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


class DzenPostPublisher:
    """Публикация готовых постов Дзен через Selenium."""

    async def publish_ready_posts(self) -> int:
        posts = await _fetch_ready_posts()
        if not posts:
            return 0
        published = 0
        for post in posts:
            uid = post.get("user_id")
            pid = post.get("id")
            await _set_last_auth_error(uid, None)

            local_paths: List[str] = []
            for p in _parse_images(post.get("images")):
                lp = await _resolve_image_file(p, pid)
                if lp:
                    local_paths.append(lp)
            post["_local_image_paths"] = local_paths

            async with get_selenium_semaphore():
                ok, pub_url, err = await asyncio.to_thread(_publish_sync, post)
            for tmp in local_paths:
                await async_fs.unlink_quiet(tmp)
            post.pop("_local_image_paths", None)

            if ok:
                await _update_post_result(post, "published", pub_url)
                published += 1
                _log_action("Published dzen post id=%s url=%s", pid, pub_url)
            else:
                await _update_post_result(post, "failed", None)
                if err:
                    await _set_last_auth_error(uid, err[:2000])
                logger.warning("Dzen post %s failed: %s", pid, err)
        return published
