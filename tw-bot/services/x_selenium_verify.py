"""Проверка входа X и чтение списка подписок (following) через Selenium — fallback при сбое OAuth."""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import ParseResult, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from database import get_db_connection, release_db_connection
from shared.auth_backoff import AuthAttemptBackoff, next_attempt_suffix, pause_active_message

from .selenium_driver import create_chrome_driver
from .selenium_errors import format_selenium_exception

logger = logging.getLogger(__name__)

X_HOME_URL = "https://x.com/home"
X_LOGIN_URL = "https://x.com/i/jf/onboarding/web?redirect_after_login=%2Fhome&mode=login"
X_BROWSER_BLOCK_MESSAGE = (
    "X отклонил браузер (HTTP 403), страница входа не открылась."
)
X_LOGIN_LIMITED_MESSAGE = (
    "X временно ограничил вход. Частые попытки продлевают ограничение."
)
X_LOGIN_LIMITED_PAUSE_SEC = 3 * 60 * 60
X_SESSION_COOKIES_REJECTED = (
    "X не принял сохранённые cookies сессии (истекли или вы вышли из аккаунта). "
    "Обновите auth_token и ct0 во вкладке «Авторизация»."
)

_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,30}$")
_X_HOSTS = frozenset({"x.com", "twitter.com", "mobile.x.com", "mobile.twitter.com"})
_LOGIN_PATH_PREFIXES = (
    "/i/flow/login",
    "/i/flow/two-factor",
    "/i/flow/verification",
    "/i/jf/onboarding",
    "/account/access",
    "/account/login_challenge",
)
_USERNAME_SELECTORS = (
    'input[name="username_or_email"]',
    'input[autocomplete^="username"]',
    'input[autocomplete="username"]',
    'input[name="text"]',
)
_NEXT_LABELS = ("Continue", "Next", "Продолжить", "Далее")
_LOGIN_BUTTON_LABELS = ("Log in", "Continue", "Войти", "Продолжить")
_COOKIE_LABELS = (
    "Refuse non-essential cookies",
    "Accept all cookies",
    "Отклонить необязательные файлы cookie",
    "Принять все файлы cookie",
)
_LOGGED_IN_SELECTORS = (
    '[data-testid="SideNav_AccountSwitcher_Button"]',
    '[data-testid="AppTabBar_Home_Link"]',
    'a[data-testid="AppTabBar_Profile_Link"]',
)
_login_backoff = AuthAttemptBackoff()


def _db_login_wait_seconds(user_id: int) -> int:
    """Срок паузы из БД. 0 — колонки нет, срок прошёл или запись не читается."""
    try:
        import psycopg2

        conn = psycopg2.connect(settings.DATABASE_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXTRACT(EPOCH FROM (twitter_login_not_before - NOW()))
                    FROM tw_profiles
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
    except Exception:
        logger.debug("X login pause read failed", exc_info=True)
        return 0
    if not row or row[0] is None:
        return 0
    remaining = float(row[0])
    if remaining <= 0:
        return 0
    return max(1, math.ceil(remaining))


def _db_set_login_pause(user_id: int, seconds: int) -> None:
    """Запоминает паузу входа, чтобы перезапуск tw-bot не отправил логин снова."""
    try:
        import psycopg2

        conn = psycopg2.connect(settings.DATABASE_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tw_profiles
                    SET twitter_login_not_before = NOW() + make_interval(secs => %s)
                    WHERE user_id = %s
                    """,
                    (int(seconds), user_id),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.warning("X login pause write failed", exc_info=True)


def x_login_block_message(user_id: int) -> Optional[str]:
    """Текст паузы, если новый вход в X сейчас нельзя. None — можно."""
    memory_wait = _login_backoff.retry_after_seconds(user_id)
    db_wait = _db_login_wait_seconds(user_id)
    wait = max(memory_wait, db_wait)
    if wait <= 0:
        return None
    if db_wait > 0:
        return f"{X_LOGIN_LIMITED_MESSAGE} {pause_active_message(wait)}"
    return pause_active_message(wait)


def note_x_login_failure(user_id: int, error: str) -> str:
    """Запоминает неудачный вход и дописывает срок следующей попытки."""
    pause = _login_backoff.record_failure(user_id)
    return f"{error} {next_attempt_suffix(pause)}"


def _db_clear_login_pause(user_id: int) -> None:
    try:
        import psycopg2

        conn = psycopg2.connect(settings.DATABASE_URL)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tw_profiles
                    SET twitter_login_not_before = NULL
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        logger.debug("X login pause clear failed", exc_info=True)


def note_x_login_success(user_id: int) -> None:
    """Успешный вход снимает паузу."""
    _login_backoff.record_success(user_id)
    _db_clear_login_pause(user_id)


def x_page_access_denied(url: str, title: str, body: str) -> bool:
    """Страница Chrome «HTTP ERROR 403», а не форма X."""
    blob = f"{url}\n{title}\n{body}".lower()
    return (
        "http error 403" in blob
        or "access to x.com was denied" in blob
        or "chrome-error://" in blob
    )


def is_x_browser_block(error: str) -> bool:
    """Отказ браузеру, а не неверный пароль. Паузу входа на это не вешаем."""
    return "http 403" in (error or "").lower()


def is_x_login_limited(text: str) -> bool:
    """X просит подождать: дальнейшие попытки только продлевают ограничение."""
    low = " ".join((text or "").lower().split())
    return "temporarily limited" in low or "временно огранич" in low


def login_form_alert_message(text: str) -> Optional[str]:
    """Ошибка role=alert на форме входа. None — это не отказ на шаге логина."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return None
    low = cleaned.lower()
    if "cookie" in low and not is_x_login_limited(cleaned):
        return None
    if is_x_login_limited(cleaned):
        return X_LOGIN_LIMITED_MESSAGE
    return f"X не пропустил логин: {cleaned[:240]}"


def report_x_login_error(user_id: Optional[int], error: str) -> str:
    if user_id is None or is_x_browser_block(error):
        return error
    if is_x_login_limited(error):
        pause = _login_backoff.record_failure(
            user_id,
            minimum_sec=X_LOGIN_LIMITED_PAUSE_SEC,
        )
        _db_set_login_pause(user_id, pause)
        return f"{error} {next_attempt_suffix(pause)}"
    return note_x_login_failure(user_id, error)


def _capture_driver_png(driver: WebDriver) -> Optional[bytes]:
    """PNG скриншота текущего окна браузера (диагностика)."""
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        logger.warning("Selenium diag: get_screenshot_as_png failed", exc_info=True)
        return None


async def _upload_diag_screenshot(user_id: int, png: bytes) -> Optional[str]:
    """
    Загрузка диагностического скриншота в S3. Ключ обязан содержать подстроку «diag».
    """
    try:
        from storage_helper import get_storage
    except Exception:
        return None
    storage = get_storage()
    if not storage or not png:
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"tw-bot/selenium/diag_tw_selenium_user{user_id}_{ts}.png"
    try:
        await storage.put(key, png, content_type="image/png")
        logger.info("Selenium diag screenshot stored s3://%s/%s", getattr(storage, "bucket", "?"), key)
        return key
    except Exception:
        logger.warning("Selenium diag: S3 upload failed", exc_info=True)
        return None


def _normalize_handle(raw: Optional[str]) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if s.startswith("@"):
        s = s[1:]
    if "x.com/" in s or "twitter.com/" in s:
        try:
            parts = s.split("/")
            for i, p in enumerate(parts):
                if p in ("x.com", "twitter.com") and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0]
        except Exception:
            pass
    return s.split("/")[0].split("?")[0]


def _parsed_x_url(url: str) -> Optional[ParseResult]:
    raw = (url or "").strip()
    if not raw:
        return None
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in _X_HOSTS:
        return None
    return parsed


def is_x_host_url(url: str) -> bool:
    """Страница на x.com / twitter.com, любой путь."""
    return _parsed_x_url(url) is not None


def is_x_home_url(url: str) -> bool:
    """True только для пути /home на x.com или twitter.com. Query не учитывается."""
    parsed = _parsed_x_url(url)
    if parsed is None:
        return False
    path = (parsed.path or "").rstrip("/") or "/"
    return path.lower() == "/home"


def is_x_login_url(url: str) -> bool:
    """Страница входа, 2FA или account/access.

    redirect_after_login=%2Fhome в query не делает адрес главной:
    «home» в строке URL ещё не значит, что лента открыта.
    """
    parsed = _parsed_x_url(url)
    if parsed is None:
        return False
    path = (parsed.path or "").lower()
    if path == "/login" or path.startswith("/login/"):
        return True
    return any(path.startswith(prefix) for prefix in _LOGIN_PATH_PREFIXES)


def has_logged_in_chrome(driver: WebDriver) -> bool:
    """Боковая навигация, которую X рисует только у вошедшей сессии."""
    for sel in _LOGGED_IN_SELECTORS:
        try:
            if driver.find_elements(By.CSS_SELECTOR, sel):
                return True
        except Exception:
            continue
    return False


def is_extra_identity_prompt(heading: str) -> bool:
    """Шаг «телефон или email» после логина. Заголовок Sign in сюда не входит."""
    text = " ".join((heading or "").lower().split())
    if not text:
        return False
    markers = (
        "enter your phone",
        "phone number or email",
        "confirm your identity",
        "verify your identity",
        "введите номер телефона",
        "номер телефона или адрес",
        "подтвердите свою личность",
        "подтвердите, что это вы",
    )
    return any(marker in text for marker in markers)


def _session_already_open(driver: WebDriver) -> bool:
    """Сессия есть, только если виден chrome или вкладки ленты.

    Самого пути /home мало: страница входа с redirect_after_login=%2Fhome
    и пустая оболочка /home ещё не авторизованы.
    """
    cur = driver.current_url or ""
    if is_x_login_url(cur):
        return False
    if has_logged_in_chrome(driver):
        return True
    if not is_x_home_url(cur):
        return False
    try:
        tabs = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid="ScrollSnap-List"] [role="tab"], '
            '[data-testid="primaryColumn"] [role="tab"]',
        )
    except Exception:
        return False
    return bool(tabs)


def _first_visible(driver: WebDriver, selectors: Tuple[str, ...]) -> Optional[WebElement]:
    for sel in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
        except Exception:
            continue
        for el in elements:
            try:
                if el.is_displayed() and el.is_enabled():
                    return el
            except Exception:
                continue
    return None


def _type_into(el: WebElement, value: str) -> None:
    el.click()
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.BACKSPACE)
    el.send_keys(value)


def _safe_click(driver: WebDriver, el: WebElement) -> bool:
    try:
        if not el.is_displayed():
            return False
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
            el,
        )
        el.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False


def _click_control(driver: WebDriver, test_ids: Tuple[str, ...], labels: Tuple[str, ...]) -> bool:
    for test_id in test_ids:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, f'[data-testid="{test_id}"]')
        except Exception:
            elements = []
        for el in elements:
            if _safe_click(driver, el):
                return True
    for label in labels:
        xpath = f"//*[normalize-space()='{label}']"
        try:
            elements = driver.find_elements(By.XPATH, xpath)
        except Exception:
            elements = []
        for el in elements:
            if _safe_click(driver, el):
                return True
    return False


def _dismiss_cookie_banner(driver: WebDriver) -> None:
    if _click_control(driver, (), _COOKIE_LABELS):
        time.sleep(0.5)


def driver_access_denied(driver: WebDriver) -> bool:
    try:
        body = driver.find_element(By.TAG_NAME, "body").text or ""
    except Exception:
        body = ""
    return x_page_access_denied(driver.current_url or "", driver.title or "", body)


def _visible_alerts(driver: WebDriver) -> str:
    chunks: List[str] = []
    try:
        nodes = driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
    except Exception:
        return ""
    for node in nodes:
        try:
            if not node.is_displayed():
                continue
            text = " ".join((node.text or "").split())
        except Exception:
            continue
        if text and text not in chunks:
            chunks.append(text)
    return "\n".join(chunks)


def _visible_headings(driver: WebDriver) -> str:
    chunks: List[str] = []
    try:
        nodes = driver.find_elements(By.CSS_SELECTOR, 'h1, [role="heading"]')
    except Exception:
        return ""
    for node in nodes:
        try:
            if not node.is_displayed():
                continue
            text = (node.text or "").strip()
        except Exception:
            continue
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def _wait_username_or_session(driver: WebDriver, timeout: float) -> Any:
    """WebElement поля логина, строка 'session', либо None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _session_already_open(driver):
            return "session"
        field = _first_visible(driver, _USERNAME_SELECTORS)
        if field is not None:
            return field
        time.sleep(0.4)
    return None


def _wait_password_step(driver: WebDriver, timeout: float) -> str:
    """password | identity | session | timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        alerts = _visible_alerts(driver)
        if is_x_login_limited(alerts):
            return "alert"
        if _first_visible(driver, ('input[name="password"]', 'input[autocomplete="current-password"]')):
            return "password"
        if login_form_alert_message(alerts):
            return "alert"
        if is_extra_identity_prompt(_visible_headings(driver)):
            return "identity"
        if _session_already_open(driver):
            return "session"
        low = (driver.current_url or "").lower()
        if "account/access" in low or "/challenge" in low:
            return "challenge"
        time.sleep(0.4)
    return "timeout"


def _login_outcome(driver: WebDriver) -> Optional[str]:
    """None — ещё ждём; 'ok' — сессия есть; иначе текст ошибки."""
    cur = driver.current_url or ""
    parsed = _parsed_x_url(cur)
    path = (parsed.path or "").lower() if parsed is not None else ""
    if "account/access" in path or "challenge" in path:
        return (
            "Требуется дополнительная проверка (2FA / challenge) — "
            "используйте OAuth или войдите вручную"
        )
    if _session_already_open(driver):
        return "ok"
    if is_extra_identity_prompt(_visible_headings(driver)) and _first_visible(
        driver, ('input[name="password"]',)
    ) is None:
        return (
            "Требуется подтверждение телефона/email — "
            "выполните вход вручную или используйте OAuth"
        )
    return None


def _challenge_message() -> str:
    return (
        "Требуется дополнительная проверка (2FA / challenge) — "
        "используйте OAuth или войдите вручную"
    )


def _identity_message() -> str:
    return (
        "Требуется подтверждение телефона/email — "
        "выполните вход вручную или используйте OAuth"
    )


def _login_x(
    driver: WebDriver,
    username: str,
    password: str,
    *,
    open_flow: bool = True,
) -> Optional[str]:
    """Логин и пароль на форме X. None — сессия открыта, обычно с возвратом на /home.

    open_flow=False оставляет текущий URL, если /home уже перенаправил на login
    (там сохранён redirect_after_login=/home).
    """
    cur = driver.current_url or ""
    if is_x_home_url(cur) and has_logged_in_chrome(driver):
        return None
    if open_flow or not is_x_login_url(cur):
        logger.info("X login: open %s", X_LOGIN_URL)
        driver.get(X_LOGIN_URL)
    else:
        logger.info("X login: continue on the login page opened from /home")

    if driver_access_denied(driver):
        return X_BROWSER_BLOCK_MESSAGE
    _dismiss_cookie_banner(driver)

    found = _wait_username_or_session(driver, 20)
    if found == "session":
        return None
    if found is None:
        if driver_access_denied(driver):
            return X_BROWSER_BLOCK_MESSAGE
        if _session_already_open(driver):
            return None
        logger.info(
            "X login: username field missing url=%s title=%s",
            driver.current_url,
            driver.title,
        )
        return "Не найдено поле логина (изменилась страница входа X)"

    _dismiss_cookie_banner(driver)
    try:
        _type_into(found, username)
    except Exception:
        return "Не удалось ввести логин на странице входа X"
    if not _click_control(driver, ("ocfEnterTextNextButton",), _NEXT_LABELS):
        found.send_keys(Keys.ENTER)

    step = _wait_password_step(driver, 25)
    if step == "session":
        return None
    if step == "identity":
        return _identity_message()
    if step == "challenge":
        return _challenge_message()
    if step != "password":
        if _session_already_open(driver):
            return None
        alert = login_form_alert_message(_visible_alerts(driver))
        if alert:
            return alert
        return "Не найдено поле пароля (возможна капча или другой шаг входа)"

    password_el = _first_visible(
        driver,
        ('input[name="password"]', 'input[autocomplete="current-password"]'),
    )
    if password_el is None:
        return "Не найдено поле пароля (возможна капча или другой шаг входа)"
    try:
        _type_into(password_el, password)
    except Exception:
        return "Не удалось ввести пароль на странице входа X"
    if not _click_control(driver, ("LoginForm_Login_Button",), _LOGIN_BUTTON_LABELS):
        password_el.send_keys(Keys.ENTER)

    deadline = time.time() + 50.0
    while time.time() < deadline:
        outcome = _login_outcome(driver)
        if outcome == "ok":
            return None
        if outcome:
            return outcome
        time.sleep(0.6)

    if _session_already_open(driver):
        return None
    return "Вход не подтверждён (неверный пароль, блокировка или антибот)"


def _collect_following_users(driver: WebDriver, max_items: int = 150) -> List[Dict[str, Optional[str]]]:
    users: List[Dict[str, Optional[str]]] = []
    seen: set[str] = set()
    scroll_n = max(1, int(getattr(settings, "X_SELENIUM_FOLLOWING_MAX_SCROLL", 4)))
    for _ in range(scroll_n):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.1)
        except Exception:
            break

    cells = driver.find_elements(By.CSS_SELECTOR, '[data-testid="UserCell"]')
    for cell in cells:
        if len(users) >= max_items:
            break
        try:
            handle: Optional[str] = None
            for a in cell.find_elements(By.CSS_SELECTOR, 'a[href^="/"], a[href^="https://x.com/"], a[href^="https://twitter.com/"]'):
                href = (a.get_attribute("href") or "").split("?")[0].rstrip("/")
                if not href:
                    continue
                if "/i/" in href or "settings" in href:
                    continue
                for base in ("https://x.com/", "https://twitter.com/"):
                    if base in href:
                        seg = href.replace(base, "").split("/")[0]
                        if seg and seg not in (
                            "following",
                            "followers",
                            "verified_followers",
                            "highlights",
                            "media",
                            "communities",
                        ):
                            if _HANDLE_RE.match(seg):
                                handle = seg
                                break
                if handle:
                    break
            if not handle or handle in seen:
                continue
            seen.add(handle)
            disp = ""
            try:
                un = cell.find_element(By.CSS_SELECTOR, '[data-testid="UserName"]')
                lines = [x.strip() for x in (un.text or "").split("\n") if x.strip()]
                if lines:
                    disp = lines[0][:200]
            except Exception:
                pass
            users.append({"id": handle, "username": handle, "name": disp or None})
        except Exception:
            continue
    return users


def verify_x_following_sync(
    login: str,
    password: str,
    handle: str,
    proxy: Optional[Dict[str, Any]],
    user_id: int,
    cookies_json: Optional[str] = None,
) -> Tuple[bool, List[Dict[str, Optional[str]]], Optional[str], Optional[bytes]]:
    """
    Вход (cookies сессии или логин/пароль) и переход на /{handle}/following.
    Возвращает (ok, users, error_or_warning, diag_png_on_failure).
    diag_png_on_failure — PNG при любой ошибке Selenium, пока сессия браузера жива.
    """
    from .x_feed_browser import _ensure_logged_in, loads_cookies

    login = (login or "").strip()
    if login.startswith("@"):
        login = login[1:].strip()
    password = (password or "").strip()
    handle = _normalize_handle(handle)
    cookies = loads_cookies(cookies_json)
    if not cookies and (not login or not password):
        return False, [], "Сохраните логин и пароль X во вкладке «Авторизация» (Twitter).", None
    if not handle:
        return False, [], "Укажите логин/ник X (@handle) для перехода к списку подписок.", None

    if not cookies:
        blocked = x_login_block_message(user_id)
        if blocked:
            return False, [], blocked, None

    if proxy and proxy.get("use_proxy"):
        pu = (proxy.get("proxy_user") or "").strip()
        pp = (proxy.get("proxy_pass") or "").strip()
        if pu or pp:
            return (
                False,
                [],
                "Прокси с логином/паролем для Selenium в этой проверке не поддерживается; отключите auth у прокси или используйте OAuth.",
                None,
            )

    driver: Optional[WebDriver] = None
    diag_png: Optional[bytes] = None

    def _fail_with_shot(msg: str) -> Tuple[bool, List[Dict[str, Optional[str]]], str, Optional[bytes]]:
        nonlocal diag_png
        if driver is not None:
            shot = _capture_driver_png(driver)
            if shot:
                diag_png = shot
        return False, [], msg, diag_png

    try:
        driver = create_chrome_driver(proxy)
        logger.debug("Selenium verify user_id=%s handle=%s", user_id, (handle[:3] + "***") if handle else "")
        err = _ensure_logged_in(driver, login, password, cookies, user_id)
        if err:
            return _fail_with_shot(err)

        following_url = f"https://x.com/{handle}/following"
        driver.get(following_url)
        time.sleep(3.0)

        try:
            WebDriverWait(driver, 30).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="UserCell"]')) > 0
                or "doesn’t follow" in (d.page_source or "").lower()
                or "does not follow" in (d.page_source or "").lower()
                or "who to follow" in (d.page_source or "").lower()
            )
        except TimeoutException:
            logger.warning("X following page: no UserCell within timeout")

        users = _collect_following_users(driver)
        warn: Optional[str] = None
        if not users:
            warn = (
                "Вход выполнен, но подписки на странице не распознаны "
                "(пустой список или изменилась вёрстка X)."
            )
            logger.info("X selenium verify: 0 user cells parsed for handle=%s", handle[:3] + "***")

        return True, users, warn, None
    except Exception as e:
        logger.exception("X selenium verify failed: %s", e)
        if driver is not None:
            shot = _capture_driver_png(driver)
            if shot:
                diag_png = shot
        return False, [], format_selenium_exception(e), diag_png
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


async def fetch_tw_credentials(
    user_id: int,
) -> Optional[Tuple[str, str, str, Dict[str, Any], Optional[str]]]:
    """Логин/пароль, ник, прокси и cookies сессии из tw_profiles. None если строки нет."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT twitter_username, twitter_password, use_proxy,
                       proxy_host, proxy_port, proxy_user, proxy_pass,
                       twitter_session_cookies
                FROM tw_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            u_raw = (row[0] or "").strip() if row[0] else ""
            pwd = row[1] if row[1] else None
            pwd_s = (pwd or "").strip() if isinstance(pwd, str) else ""
            use_proxy = bool(row[2])
            proxy_host = (row[3] or "").strip() if row[3] else ""
            proxy_port = row[4]
            proxy_user = (row[5] or "").strip() if row[5] else ""
            proxy_pass = (row[6] or "").strip() if row[6] else ""
            proxy: Dict[str, Any] = {
                "use_proxy": use_proxy,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "proxy_user": proxy_user,
                "proxy_pass": proxy_pass,
            }
            if use_proxy and proxy_host:
                proxy["host"] = proxy_host
                proxy["port"] = int(proxy_port) if proxy_port is not None else 80
            hnorm = _normalize_handle(u_raw)
            return u_raw, pwd_s, hnorm, proxy, row[7]
    finally:
        await release_db_connection(conn)


async def verify_x_for_user(user_id: int) -> Dict[str, Any]:
    """Проверка по учётным данным из БД (без передачи пароля из UI)."""
    row = await fetch_tw_credentials(user_id)
    if row is None:
        return {
            "ok": False,
            "method": "selenium",
            "users": [],
            "error": "Профиль Twitter не найден. Сохраните настройки на вкладке «Авторизация».",
        }
    username_raw, password, handle, proxy, cookies_json = row
    if not password and not (cookies_json or "").strip():
        return {
            "ok": False,
            "method": "selenium",
            "users": [],
            "error": "Сохраните пароль X или cookies сессии (вкладка «Авторизация»).",
        }

    login_identifier = (username_raw or handle or "").strip()
    ok, users, msg, diag_png = await asyncio.to_thread(
        verify_x_following_sync,
        login_identifier,
        password,
        handle or login_identifier,
        proxy,
        user_id,
        cookies_json,
    )

    diag_s3_key: Optional[str] = None
    if diag_png:
        diag_s3_key = await _upload_diag_screenshot(user_id, diag_png)

    if ok:
        out: Dict[str, Any] = {"ok": True, "method": "selenium", "users": users}
        if msg:
            out["message"] = msg
        return out

    err_text = (msg or "Ошибка проверки Selenium")[:2000]
    err_out: Dict[str, Any] = {
        "ok": False,
        "method": "selenium",
        "users": [],
        "error": err_text,
    }
    if diag_s3_key:
        err_out["diag_s3_key"] = diag_s3_key
    return err_out
