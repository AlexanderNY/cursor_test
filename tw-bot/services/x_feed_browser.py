"""Чтение ленты X через Selenium: Following (home) и таймлайн пользователя (@handle)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Set, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings

from .selenium_driver import create_chrome_driver, get_selenium_semaphore
from .selenium_errors import format_selenium_exception
from .x_selenium_verify import _capture_driver_png, _login_x, _normalize_handle

logger = logging.getLogger(__name__)

_STATUS_ID_RE = re.compile(r"/status(?:es)?/(\d+)", re.IGNORECASE)
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
class FeedTweet:
    """Один пост из UI-ленты Following."""

    status_id: str
    text: str
    url: str
    screenshot_png: Optional[bytes] = None
    screenshot_path: Optional[str] = None


@dataclass
class FeedCollectResult:
    """Результат одного прохода браузерного сбора."""

    ok: bool
    tweets: List[FeedTweet] = field(default_factory=list)
    cookies_json: Optional[str] = None
    error: Optional[str] = None
    diag_png: Optional[bytes] = None


def extract_status_id(href_or_url: str) -> Optional[str]:
    """Достаёт numeric status id из любого href X (/user/status/N или /i/web/status/N)."""
    raw = (href_or_url or "").strip()
    if not raw:
        return None
    match = _STATUS_ID_RE.search(raw.split("?")[0].split("#")[0])
    if not match:
        return None
    return match.group(1)


def canonical_status_url(status_id: str) -> str:
    """Канонический URL поста — тот же ключ, что у API-сбора в feed_collector."""
    tid = (status_id or "").strip()
    return f"https://x.com/i/web/status/{tid}"


def parse_tweet_card_fields(
    status_hrefs: List[str],
    tweet_text: str,
) -> Optional[Dict[str, str]]:
    """
    Собирает {status_id, text, url} из уже извлечённых строк карточки.
    Без Selenium — для юнит-тестов и парсера DOM.
    """
    status_id: Optional[str] = None
    for href in status_hrefs:
        status_id = extract_status_id(href)
        if status_id:
            break
    if not status_id:
        return None
    text = (tweet_text or "").strip()
    return {
        "status_id": status_id,
        "text": text,
        "url": canonical_status_url(status_id),
    }


def dumps_cookies(cookies: List[Dict[str, Any]]) -> str:
    """Сериализация cookies Selenium в JSON (без логирования значений)."""
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
    """Десериализация cookies; пустой/битый JSON → []."""
    raw = (cookies_json or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict) and item.get("name") and "value" in item:
            out.append(item)
    return out


def compress_png_to_jpeg(png_bytes: bytes, max_side: int = 1920, quality: int = 85) -> bytes:
    """PNG → JPEG (resize по длинной стороне). Без Pillow возвращает исходные байты."""
    if not png_bytes:
        return b""
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed; storing screenshot as PNG bytes")
        return png_bytes
    try:
        img = Image.open(BytesIO(png_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        width, height = img.size
        if width > max_side or height > max_side:
            if width >= height:
                new_w, new_h = max_side, max(1, int(height * max_side / width))
            else:
                new_w, new_h = max(1, int(width * max_side / height)), max_side
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        logger.warning("Screenshot compress failed", exc_info=True)
        return png_bytes


def _is_login_url(url: str) -> bool:
    cur = (url or "").lower()
    return "login" in cur or "flow/login" in cur or "challenge" in cur or "account/access" in cur


def _apply_cookies(driver: WebDriver, cookies: List[Dict[str, Any]]) -> None:
    if not cookies:
        return
    driver.get("https://x.com")
    time.sleep(1.0)
    for cookie in cookies:
        try:
            payload = dict(cookie)
            # Selenium add_cookie rejects expiry as float in some versions
            if "expiry" in payload:
                try:
                    payload["expiry"] = int(payload["expiry"])
                except (TypeError, ValueError):
                    payload.pop("expiry", None)
            # sameSite None / empty breaks some chromedrivers
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


def _click_following_tab(driver: WebDriver) -> None:
    """Переключает Home на вкладку Following (хронология подписок)."""
    selectors = (
        'a[role="tab"][href="/home"]',
        'div[role="tablist"] a[role="tab"]',
        'nav[aria-label="Home timeline"] a[role="tab"]',
    )
    for sel in selectors:
        try:
            tabs = driver.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            tabs = []
        for tab in tabs:
            try:
                label = (tab.text or tab.get_attribute("aria-label") or "").strip().lower()
                if "following" in label or "подписки" in label:
                    tab.click()
                    time.sleep(1.5)
                    return
            except Exception:
                continue
    # Fallback: второй tab в списке (For you / Following)
    try:
        tabs = driver.find_elements(By.CSS_SELECTOR, 'a[role="tab"]')
        if len(tabs) >= 2:
            tabs[1].click()
            time.sleep(1.5)
    except Exception:
        pass


def _article_status_hrefs(article: WebElement) -> List[str]:
    hrefs: List[str] = []
    try:
        links = article.find_elements(By.CSS_SELECTOR, 'a[href*="/status/"]')
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


def _article_tweet_text(article: WebElement) -> str:
    try:
        el = article.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
        return (el.text or "").strip()
    except Exception:
        return (article.text or "").strip()[:2000]


def _parse_article(article: WebElement) -> Optional[Dict[str, str]]:
    return parse_tweet_card_fields(_article_status_hrefs(article), _article_tweet_text(article))


def _screenshot_article(article: WebElement) -> Optional[bytes]:
    try:
        png = article.screenshot_as_png
        return png if png else None
    except Exception:
        logger.debug("article screenshot failed", exc_info=True)
        return None


def _scroll_collect_articles(
    driver: WebDriver,
    *,
    known_status_ids: Set[str],
    take_screenshot: bool,
    max_scroll: int,
    max_tweets: int,
) -> List[FeedTweet]:
    collected: List[FeedTweet] = []
    seen_ids: Set[str] = set()
    scroll_n = max(1, int(max_scroll))
    limit = max(1, int(max_tweets))

    for round_i in range(scroll_n):
        try:
            articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
        except Exception:
            articles = []

        visible_ids: List[str] = []
        new_this_round = 0
        for article in articles:
            if len(collected) >= limit:
                break
            parsed = _parse_article(article)
            if not parsed:
                continue
            sid = parsed["status_id"]
            visible_ids.append(sid)
            if sid in known_status_ids or sid in seen_ids:
                continue
            seen_ids.add(sid)
            shot = _screenshot_article(article) if take_screenshot else None
            collected.append(
                FeedTweet(
                    status_id=sid,
                    text=parsed["text"],
                    url=parsed["url"],
                    screenshot_png=shot,
                )
            )
            new_this_round += 1

        if len(collected) >= limit:
            break
        if visible_ids and new_this_round == 0:
            break
        if round_i + 1 < scroll_n:
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2)
            except Exception:
                break
    return collected


def _ensure_logged_in(
    driver: WebDriver,
    login: str,
    password: str,
    cookies: List[Dict[str, Any]],
) -> Optional[str]:
    """Returns error message or None on success."""
    logged_in = False
    if cookies:
        _apply_cookies(driver, cookies)
        driver.get("https://x.com/home")
        time.sleep(2.5)
        if not _is_login_url(driver.current_url or ""):
            logged_in = True

    if not logged_in:
        err = _login_x(driver, login, password)
        if err:
            return err
        driver.get("https://x.com/home")
        time.sleep(2.0)
        if _is_login_url(driver.current_url or ""):
            return "Сессия не установлена после входа (логин/challenge)"
    return None


def _browser_collect_sync(
    *,
    login: str,
    password: str,
    cookies_json: Optional[str],
    proxy: Optional[Dict[str, Any]],
    take_screenshot: bool,
    known_status_ids: Set[str],
    max_scroll: int,
    max_tweets: int,
    after_login,
    empty_feed_error: str,
) -> FeedCollectResult:
    """
    Shared Selenium session: login → after_login(driver) → scroll tweet cards.
    after_login navigates to the target feed and returns Optional[str] error.
    """
    login = (login or "").strip()
    if login.startswith("@"):
        login = login[1:].strip()
    password = (password or "").strip()
    if not login or not password:
        return FeedCollectResult(
            ok=False,
            error="Сохраните логин и пароль X во вкладке «Авторизация» (Twitter).",
        )

    if proxy and proxy.get("use_proxy"):
        proxy_user = (proxy.get("proxy_user") or "").strip()
        proxy_pass = (proxy.get("proxy_pass") or "").strip()
        if proxy_user or proxy_pass:
            return FeedCollectResult(
                ok=False,
                error=(
                    "Прокси с логином/паролем для Selenium не поддерживается; "
                    "отключите auth у прокси."
                ),
            )

    cookies = loads_cookies(cookies_json)
    driver: Optional[WebDriver] = None
    diag_png: Optional[bytes] = None

    def _fail(msg: str) -> FeedCollectResult:
        nonlocal diag_png
        if driver is not None:
            shot = _capture_driver_png(driver)
            if shot:
                diag_png = shot
        return FeedCollectResult(ok=False, error=msg, diag_png=diag_png)

    try:
        driver = create_chrome_driver(proxy)
        login_err = _ensure_logged_in(driver, login, password, cookies)
        if login_err:
            return _fail(login_err)

        nav_err = after_login(driver)
        if nav_err:
            return _fail(nav_err)

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
        except TimeoutException:
            return _fail(empty_feed_error)

        collected = _scroll_collect_articles(
            driver,
            known_status_ids=known_status_ids,
            take_screenshot=take_screenshot,
            max_scroll=max_scroll,
            max_tweets=max_tweets,
        )
        cookies_out = _dump_driver_cookies(driver)
        return FeedCollectResult(ok=True, tweets=collected, cookies_json=cookies_out)
    except Exception as exc:
        logger.exception("X feed browser collect failed: %s", exc)
        if driver is not None:
            shot = _capture_driver_png(driver)
            if shot:
                diag_png = shot
        return FeedCollectResult(
            ok=False,
            error=format_selenium_exception(exc),
            diag_png=diag_png,
        )
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def collect_following_feed_sync(
    login: str,
    password: str,
    cookies_json: Optional[str],
    proxy: Optional[Dict[str, Any]],
    take_screenshot: bool,
    known_status_ids: Set[str],
    max_scroll: int,
    max_tweets: int,
) -> FeedCollectResult:
    """
    Вход (cookies или логин/пароль) → Home / Following → карточки article.
    known_status_ids — уже сохранённые status id; скролл останавливается, когда
    все видимые посты уже известны.
    """

    def _after(driver: WebDriver) -> Optional[str]:
        _click_following_tab(driver)
        return None

    return _browser_collect_sync(
        login=login,
        password=password,
        cookies_json=cookies_json,
        proxy=proxy,
        take_screenshot=take_screenshot,
        known_status_ids=known_status_ids,
        max_scroll=max_scroll,
        max_tweets=max_tweets,
        after_login=_after,
        empty_feed_error=(
            "Лента Following не загрузилась (нет карточек tweet — изменилась вёрстка или пустая лента)."
        ),
    )


def collect_user_timeline_sync(
    login: str,
    password: str,
    cookies_json: Optional[str],
    proxy: Optional[Dict[str, Any]],
    take_screenshot: bool,
    known_status_ids: Set[str],
    max_scroll: int,
    max_tweets: int,
    handle: str,
) -> FeedCollectResult:
    """
    Вход → профиль https://x.com/{handle} → карточки article.
    Основной способ чтения brand-канала Twitter (API часто недоступен на Free).
    """
    target = _normalize_handle(handle)
    if not target:
        return FeedCollectResult(ok=False, error="Пустой @handle канала Twitter")

    def _after(driver: WebDriver) -> Optional[str]:
        driver.get(f"https://x.com/{target}")
        time.sleep(2.5)
        if _is_login_url(driver.current_url or ""):
            return "Сессия сброшена при открытии профиля"
        cur = (driver.current_url or "").lower()
        if "/i/flow/" in cur or "account/access" in cur:
            return "X запросил challenge при открытии профиля"
        return None

    return _browser_collect_sync(
        login=login,
        password=password,
        cookies_json=cookies_json,
        proxy=proxy,
        take_screenshot=take_screenshot,
        known_status_ids=known_status_ids,
        max_scroll=max_scroll,
        max_tweets=max_tweets,
        after_login=_after,
        empty_feed_error=(
            f"Лента @{target} не загрузилась (нет карточек tweet — приватный аккаунт, "
            "пустой профиль или изменилась вёрстка)."
        ),
    )


async def upload_feed_screenshot(user_id: int, png_bytes: bytes) -> Optional[str]:
    """JPEG в S3 uploads/url/...; путь для UI: /uploads/url/{user_id}/{date}/{uuid}.jpg."""
    if not png_bytes:
        return None
    jpeg = compress_png_to_jpeg(png_bytes)
    if not jpeg:
        return None
    try:
        from storage_helper import get_storage
    except Exception:
        return None
    storage = get_storage()
    if not storage:
        return None
    date_part = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = f"{uuid.uuid4().hex}.jpg"
    key = f"uploads/url/{user_id}/{date_part}/{name}"
    try:
        await storage.put(key, jpeg, content_type="image/jpeg")
        return f"/uploads/url/{user_id}/{date_part}/{name}"
    except Exception:
        logger.warning("Feed screenshot S3 upload failed", exc_info=True)
        return None


async def _upload_tweet_shots(
    user_id: int,
    result: FeedCollectResult,
    take_screenshot: bool,
) -> FeedCollectResult:
    if not result.ok or not take_screenshot:
        return result
    for tweet in result.tweets:
        if tweet.screenshot_png:
            tweet.screenshot_path = await upload_feed_screenshot(user_id, tweet.screenshot_png)
            tweet.screenshot_png = None
    return result


async def collect_following_feed_for_profile(
    login: str,
    password: str,
    cookies_json: Optional[str],
    proxy: Optional[Dict[str, Any]],
    take_screenshot: bool,
    known_status_ids: Set[str],
    user_id: int,
) -> FeedCollectResult:
    """Async-обёртка: семафор Chrome + загрузка скринов карточек."""
    max_scroll = int(getattr(settings, "X_SELENIUM_FOLLOWING_MAX_SCROLL", 4) or 4)
    max_tweets = int(getattr(settings, "X_FEED_BROWSER_MAX_TWEETS", 30) or 30)
    sem = get_selenium_semaphore()
    await sem.acquire()
    try:
        result = await asyncio.to_thread(
            collect_following_feed_sync,
            login,
            password,
            cookies_json,
            proxy,
            take_screenshot,
            known_status_ids,
            max_scroll,
            max_tweets,
        )
    finally:
        sem.release()
    return await _upload_tweet_shots(user_id, result, take_screenshot)


async def collect_user_timeline_for_profile(
    login: str,
    password: str,
    cookies_json: Optional[str],
    proxy: Optional[Dict[str, Any]],
    take_screenshot: bool,
    known_status_ids: Set[str],
    user_id: int,
    handle: str,
) -> FeedCollectResult:
    """Async: таймлайн конкретного @handle (brand channel)."""
    max_scroll = int(getattr(settings, "X_SELENIUM_FOLLOWING_MAX_SCROLL", 4) or 4)
    max_tweets = int(getattr(settings, "X_FEED_BROWSER_MAX_TWEETS", 30) or 30)
    sem = get_selenium_semaphore()
    await sem.acquire()
    try:
        result = await asyncio.to_thread(
            collect_user_timeline_sync,
            login,
            password,
            cookies_json,
            proxy,
            take_screenshot,
            known_status_ids,
            max_scroll,
            max_tweets,
            handle,
        )
    finally:
        sem.release()
    return await _upload_tweet_shots(user_id, result, take_screenshot)


def normalize_login_handle(username_raw: str, handle_hint: str = "") -> Tuple[str, str]:
    """Возвращает (login_identifier, handle) без @."""
    handle = _normalize_handle(handle_hint or username_raw)
    login = (username_raw or handle or "").strip()
    if login.startswith("@"):
        login = login[1:].strip()
    return login, handle
