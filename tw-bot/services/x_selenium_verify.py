"""Проверка входа X и чтение списка подписок (following) через Selenium — fallback при сбое OAuth."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from database import get_db_connection, release_db_connection

from .selenium_driver import create_chrome_driver
from .selenium_errors import format_selenium_exception

logger = logging.getLogger(__name__)

_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,30}$")


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


def _login_x(driver: WebDriver, username: str, password: str) -> Optional[str]:
    """Вход через x.com/i/flow/login. Возвращает текст ошибки или None при успехе."""
    driver.get("https://x.com/i/flow/login")
    time.sleep(2.0)

    username_el = None
    for sel in ('input[autocomplete="username"]', 'input[name="text"]'):
        try:
            username_el = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sel))
            )
            break
        except TimeoutException:
            continue
    if username_el is None:
        return "Не найдено поле логина (изменилась страница входа X)"

    username_el.clear()
    username_el.send_keys(username)
    username_el.send_keys(Keys.ENTER)
    time.sleep(2.5)

    src = (driver.page_source or "").lower()
    if "phone" in src and "email" in driver.page_source.lower() and "confirm" in src:
        return "Требуется подтверждение телефона/email — выполните вход вручную или используйте OAuth"

    try:
        password_el = WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
    except TimeoutException:
        cur = (driver.current_url or "").lower()
        if "challenge" in cur or "account/access" in cur:
            return "Требуется дополнительная проверка (2FA / challenge) — используйте OAuth или войдите вручную"
        return "Не найдено поле пароля (возможна капча или другой шаг входа)"

    password_el.clear()
    password_el.send_keys(password)
    password_el.send_keys(Keys.ENTER)

    deadline = time.time() + 50.0
    while time.time() < deadline:
        cur = (driver.current_url or "").lower()
        if "challenge" in cur or "account/access" in cur:
            return "Требуется дополнительная проверка (2FA / challenge) — используйте OAuth"
        if "login" not in cur and "flow" not in cur:
            return None
        if "home" in cur or "/compose" in cur or cur.rstrip("/").endswith("x.com/home"):
            return None
        time.sleep(0.6)

    cur = (driver.current_url or "").lower()
    if "login" in cur or "flow/login" in cur:
        return "Вход не подтверждён (неверный пароль, блокировка или антибот)"
    return None


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
) -> Tuple[bool, List[Dict[str, Optional[str]]], Optional[str], Optional[bytes]]:
    """
    Вход и переход на /{handle}/following.
    Возвращает (ok, users, error_or_warning, diag_png_on_failure).
    diag_png_on_failure — PNG при любой ошибке Selenium, пока сессия браузера жива.
    """
    login = (login or "").strip()
    if login.startswith("@"):
        login = login[1:].strip()
    password = (password or "").strip()
    handle = _normalize_handle(handle)
    if not login or not password:
        return False, [], "Сохраните логин и пароль X во вкладке «Авторизация» (Twitter).", None
    if not handle:
        return False, [], "Укажите логин/ник X (@handle) для перехода к списку подписок.", None

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
        err = _login_x(driver, login, password)
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
) -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
    """Логин/пароль и ник из tw_profiles + данные прокси. None если строки нет."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT twitter_username, twitter_password, use_proxy,
                       proxy_host, proxy_port, proxy_user, proxy_pass
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
            return u_raw, pwd_s, hnorm, proxy
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
    username_raw, password, handle, proxy = row
    if not password:
        return {
            "ok": False,
            "method": "selenium",
            "users": [],
            "error": "Сохраните пароль X в профиле (вкладка «Авторизация»).",
        }

    login_identifier = (username_raw or handle or "").strip()
    ok, users, msg, diag_png = await asyncio.to_thread(
        verify_x_following_sync,
        login_identifier,
        password,
        handle or login_identifier,
        proxy,
        user_id,
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
