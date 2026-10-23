"""Чтение профиля Threads (threads.net/@handle) через Selenium после входа в Instagram."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from services.selenium_driver import create_chrome_driver, get_selenium_semaphore

logger = logging.getLogger(__name__)

_POST_ID_RE = re.compile(
    r"(?:threads\.net/(?:@[^/]+/)?(?:post|t)/([A-Za-z0-9_-]+)|/post/([A-Za-z0-9_-]+))",
    re.IGNORECASE,
)
_COOKIE_EXPORT_KEYS = (
    "name",
    "value",
    "domain",
    "path",
    "expiry",
    "secure",
    "httpOnly",
    "sameSite",
)


@dataclass
class FeedPost:
    post_id: str
    text: str
    url: str
    screenshot_png: Optional[bytes] = None
    screenshot_path: Optional[str] = None


@dataclass
class FeedCollectResult:
    ok: bool
    posts: List[FeedPost] = field(default_factory=list)
    cookies_json: Optional[str] = None
    error: Optional[str] = None
    diag_png: Optional[bytes] = None


def normalize_handle(raw: str) -> str:
    h = (raw or "").strip()
    if h.startswith("@"):
        h = h[1:].strip()
    return h.split("/")[0].split("?")[0].strip()


def extract_post_id(href_or_url: str) -> Optional[str]:
    raw = (href_or_url or "").strip()
    if not raw:
        return None
    match = _POST_ID_RE.search(raw.split("?")[0].split("#")[0])
    if not match:
        return None
    return match.group(1) or match.group(2)


def canonical_post_url(post_id: str, handle: str = "") -> str:
    tid = (post_id or "").strip()
    if not tid:
        return ""
    h = normalize_handle(handle)
    if h:
        return f"https://www.threads.net/@{h}/post/{tid}"
    return f"https://www.threads.net/t/{tid}"


def parse_post_card_fields(
    hrefs: List[str],
    text: str,
    handle: str = "",
) -> Optional[Dict[str, str]]:
    """Pure parser for unit tests — no Selenium."""
    post_id: Optional[str] = None
    for href in hrefs:
        post_id = extract_post_id(href)
        if post_id:
            break
    if not post_id:
        return None
    body = (text or "").strip()
    return {
        "post_id": post_id,
        "text": body,
        "url": canonical_post_url(post_id, handle),
    }


def dumps_cookies(cookies: List[Dict[str, Any]]) -> str:
    cleaned: List[Dict[str, Any]] = []
    for cookie in cookies or []:
        if not isinstance(cookie, dict) or not cookie.get("name"):
            continue
        row: Dict[str, Any] = {}
        for key in _COOKIE_EXPORT_KEYS:
            if key in cookie and cookie[key] is not None:
                row[key] = cookie[key]
        cleaned.append(row)
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))


def loads_cookies(cookies_json: Optional[str]) -> List[Dict[str, Any]]:
    raw = (cookies_json or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("name") and "value" in item]


def _is_login_url(url: str) -> bool:
    cur = (url or "").lower()
    return "login" in cur or "accounts/login" in cur or "challenge" in cur or "checkpoint" in cur


def _apply_cookies(driver: WebDriver, cookies: List[Dict[str, Any]]) -> None:
    if not cookies:
        return
    driver.get("https://www.instagram.com/")
    time.sleep(1.0)
    for cookie in cookies:
        try:
            payload = dict(cookie)
            if "expiry" in payload:
                try:
                    payload["expiry"] = int(payload["expiry"])
                except (TypeError, ValueError):
                    payload.pop("expiry", None)
            same_site = payload.get("sameSite")
            if same_site is None or same_site == "":
                payload.pop("sameSite", None)
            driver.add_cookie(payload)
        except Exception:
            continue


def _dump_driver_cookies(driver: WebDriver) -> str:
    try:
        return dumps_cookies(driver.get_cookies() or [])
    except Exception:
        return "[]"


def _capture_diag_png(driver: Optional[WebDriver]) -> Optional[bytes]:
    if not driver:
        return None
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        return None


def _login_instagram(driver: WebDriver, login: str, password: str) -> Optional[str]:
    """Returns error message or None."""
    try:
        import services.instagram_selenium_helpers as ig
        from selenium.webdriver.common.keys import Keys

        driver.get(settings.INSTAGRAM_WEB_LOGIN_URL)
        time.sleep(2.0)
        wait = WebDriverWait(driver, 25)
        if not ig.find_email_input_and_fill(driver, login, wait):
            return "Не найдена форма логина Instagram"
        time.sleep(0.4)
        if not ig.find_password_input_and_fill(driver, password, wait):
            return "Не найдено поле пароля Instagram"
        time.sleep(0.3)
        if not ig.find_and_click_login_button(driver, wait):
            try:
                pass_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pass_el.send_keys(Keys.RETURN)
            except Exception:
                return "Не найдена кнопка входа Instagram"
        time.sleep(4.0)
        url = (driver.current_url or "").lower()
        if _is_login_url(url) and "onetap" not in url:
            if "challenge" in url or "checkpoint" in url or "two_factor" in url:
                return "Instagram запросил challenge/2FA — завершите вход вручную"
            return "Не удалось войти в Instagram (проверьте логин/пароль)"
        return None
    except Exception as exc:
        return f"Ошибка входа Instagram: {exc}"


def _article_hrefs(article) -> List[str]:
    hrefs: List[str] = []
    try:
        links = article.find_elements(By.CSS_SELECTOR, "a[href*='/post/'], a[href*='/t/']")
    except Exception:
        return hrefs
    for link in links:
        try:
            href = (link.get_attribute("href") or "").strip()
        except Exception:
            continue
        if href:
            hrefs.append(href)
    return hrefs


def _article_text(article) -> str:
    try:
        return (article.text or "").strip()[:4000]
    except Exception:
        return ""


def collect_user_timeline_sync(
    login: str,
    password: str,
    cookies_json: Optional[str],
    take_screenshot: bool,
    known_post_ids: Set[str],
    max_scroll: int,
    max_posts: int,
    handle: str,
) -> FeedCollectResult:
    """
    Вход Instagram → threads.net/@handle → карточки постов.
    Основной путь чтения brand-каналов (API Meta редко отдаёт чужие ленты).
    """
    login = (login or "").strip()
    if login.startswith("@"):
        login = login[1:].strip()
    password = (password or "").strip()
    target = normalize_handle(handle)
    if not target:
        return FeedCollectResult(ok=False, error="Пустой @handle канала Threads")
    if not login or not password:
        return FeedCollectResult(
            ok=False,
            error="Сохраните логин и пароль Meta/Instagram на вкладке «Авторизация» (Threads).",
        )

    cookies = loads_cookies(cookies_json)
    driver: Optional[WebDriver] = None
    diag_png: Optional[bytes] = None

    def _fail(msg: str) -> FeedCollectResult:
        nonlocal diag_png
        if driver is not None:
            shot = _capture_diag_png(driver)
            if shot:
                diag_png = shot
        return FeedCollectResult(ok=False, error=msg, diag_png=diag_png)

    try:
        driver = create_chrome_driver()
        logged_in = False
        if cookies:
            _apply_cookies(driver, cookies)
            driver.get("https://www.threads.net/")
            time.sleep(2.0)
            if not _is_login_url(driver.current_url or ""):
                logged_in = True

        if not logged_in:
            err = _login_instagram(driver, login, password)
            if err:
                return _fail(err)

        driver.get(f"https://www.threads.net/@{target}")
        time.sleep(2.5)
        if _is_login_url(driver.current_url or ""):
            return _fail("Сессия сброшена при открытии профиля Threads")

        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/post/'], a[href*='/t/'], article, [data-pressable-container]")
                )
            )
        except TimeoutException:
            return _fail(
                f"Лента @{target} не загрузилась (пустой профиль, приватность или смена вёрстки)."
            )

        collected: List[FeedPost] = []
        seen: Set[str] = set()
        scroll_n = max(1, int(max_scroll))
        limit = max(1, int(max_posts))

        for round_i in range(scroll_n):
            try:
                articles = driver.find_elements(
                    By.CSS_SELECTOR,
                    "article, div[data-pressable-container='true'], div[role='article']",
                )
            except Exception:
                articles = []
            if not articles:
                # Fallback: scan all post links on page
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/post/'], a[href*='/t/']")
                except Exception:
                    links = []
                for link in links:
                    if len(collected) >= limit:
                        break
                    try:
                        href = (link.get_attribute("href") or "").strip()
                    except Exception:
                        continue
                    pid = extract_post_id(href)
                    if not pid or pid in known_post_ids or pid in seen:
                        continue
                    seen.add(pid)
                    try:
                        text = (link.find_element(By.XPATH, "./ancestor::*[self::div or self::article][1]").text or "")[
                            :4000
                        ]
                    except Exception:
                        text = ""
                    collected.append(
                        FeedPost(
                            post_id=pid,
                            text=text.strip(),
                            url=canonical_post_url(pid, target),
                        )
                    )
            else:
                for article in articles:
                    if len(collected) >= limit:
                        break
                    parsed = parse_post_card_fields(
                        _article_hrefs(article),
                        _article_text(article),
                        target,
                    )
                    if not parsed:
                        continue
                    pid = parsed["post_id"]
                    if pid in known_post_ids or pid in seen:
                        continue
                    seen.add(pid)
                    shot = None
                    if take_screenshot:
                        try:
                            shot = article.screenshot_as_png
                        except Exception:
                            shot = None
                    collected.append(
                        FeedPost(
                            post_id=pid,
                            text=parsed["text"],
                            url=parsed["url"],
                            screenshot_png=shot,
                        )
                    )

            if len(collected) >= limit:
                break
            if round_i + 1 < scroll_n:
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.4)
                except Exception:
                    break

        cookies_out = _dump_driver_cookies(driver)
        return FeedCollectResult(ok=True, posts=collected, cookies_json=cookies_out)
    except WebDriverException as exc:
        logger.exception("Threads feed browser failed: %s", exc)
        if driver is not None:
            diag_png = _capture_diag_png(driver)
        return FeedCollectResult(ok=False, error=str(exc)[:500], diag_png=diag_png)
    except Exception as exc:
        logger.exception("Threads feed browser failed: %s", exc)
        if driver is not None:
            diag_png = _capture_diag_png(driver)
        return FeedCollectResult(ok=False, error=str(exc)[:500], diag_png=diag_png)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


async def collect_user_timeline_for_profile(
    login: str,
    password: str,
    cookies_json: Optional[str],
    take_screenshot: bool,
    known_post_ids: Set[str],
    user_id: int,
    handle: str,
) -> FeedCollectResult:
    max_scroll = int(getattr(settings, "THREADS_FEED_MAX_SCROLL", 4) or 4)
    max_posts = int(getattr(settings, "THREADS_FEED_MAX_POSTS", 30) or 30)
    sem = get_selenium_semaphore()
    await sem.acquire()
    try:
        result = await asyncio.to_thread(
            collect_user_timeline_sync,
            login,
            password,
            cookies_json,
            take_screenshot,
            known_post_ids,
            max_scroll,
            max_posts,
            handle,
        )
    finally:
        sem.release()

    if not result.ok or not take_screenshot:
        return result

    for post in result.posts:
        if post.screenshot_png:
            post.screenshot_path = await _upload_feed_screenshot(user_id, post.screenshot_png)
            post.screenshot_png = None
    return result


async def _upload_feed_screenshot(user_id: int, png_bytes: bytes) -> Optional[str]:
    if not png_bytes:
        return None
    try:
        from services.selenium_diag_upload import upload_selenium_diagnostic_png
    except Exception:
        return None
    # Reuse diag uploader path pattern; key still usable as screenshot path in UI.
    try:
        key = await upload_selenium_diagnostic_png(user_id, 0, png_bytes)
        if key:
            return f"/uploads/{key}" if not str(key).startswith("/") else str(key)
    except Exception:
        logger.debug("feed screenshot upload failed", exc_info=True)
    return None
