"""Резервная проверка VK: вход через Selenium и сбор списка сообществ с веб-страницы (без API-токена)."""

from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from services.selenium_driver import create_chrome_driver
from storage_helper import put_bytes_sync

logger = logging.getLogger(__name__)


def _save_diagnostic_screenshot(driver: WebDriver, user_id: Optional[int]) -> Optional[str]:
    """
    PNG скриншот текущего окна браузера в S3. Имя ключа содержит подстроку 'diag'.
    При отключённом S3 возвращает None (ошибка логируется в put_bytes_sync).
    """
    try:
        png = driver.get_screenshot_as_png()
    except Exception as e:
        logger.warning("VK Selenium: diagnostic screenshot capture failed: %s", e)
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid_part = str(user_id) if user_id is not None else "na"
    # Обязательное вхождение "diag" в имя объекта
    key = f"vk/selenium/vk_selenium_diag_uid{uid_part}_{ts}_{uuid.uuid4().hex[:10]}.png"
    return put_bytes_sync(key, png, "image/png")


def _url_looks_logged_in(url: str) -> bool:
    u = (url or "").lower()
    if "oauth.vk.com" in u:
        return False
    if "vk.com/login" in u or "m.vk.com/login" in u:
        return False
    if "act=login" in u or "act=auth" in u:
        return False
    if "/feed" in u or "/im" in u or "/groups" in u:
        return True
    if re.search(r"vk\.com/id\d+", u):
        return True
    return False


# Ссылки на сообщества VK в ленте /groups
_GROUP_HREF = re.compile(
    r"https?://(?:[\w.-]+\.)?vk\.com/(?:club|public|event)(\d+)",
    re.IGNORECASE,
)
_SCREEN_NAME = re.compile(r"https?://(?:[\w.-]+\.)?vk\.com/([a-zA-Z0-9._-]+)/?$")


def _page_text_suspicious(driver: WebDriver) -> Optional[str]:
    """Возвращает код причины, если похоже на капчу или 2FA."""
    try:
        body = (driver.page_source or "").lower()
        page_url = (driver.current_url or "").lower()
    except Exception:
        return None
    if "smartcaptcha" in body or "hcaptcha" in body:
        return "captcha"
    if "captcha" in body and ("vk.com" in page_url or "vk.ru" in page_url):
        return "captcha"
    if "введите код" in body or "sms" in body and "подтвержд" in body:
        return "twofa"
    if "двухфакторн" in body or "two-factor" in body:
        return "twofa"
    return None


def _find_login_inputs(driver: WebDriver, wait: WebDriverWait):
    """Находит поля логина и пароля (вёрстка VK меняется — несколько вариантов)."""
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        pass
    login_el = None
    pass_el = None
    for by, sel in [
        (By.CSS_SELECTOR, "#index_email"),
        (By.CSS_SELECTOR, "input[name='login']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
    ]:
        try:
            els = driver.find_elements(by, sel)
            if els:
                login_el = els[0]
                break
        except Exception:
            continue
    if not login_el:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            login_el = els[0] if els else None
        except Exception:
            login_el = None
    for by, sel in [
        (By.CSS_SELECTOR, "#index_pass"),
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]:
        try:
            els = driver.find_elements(by, sel)
            if els:
                pass_el = els[0]
                break
        except Exception:
            continue
    return login_el, pass_el


def _submit_login(driver: WebDriver) -> None:
    for sel in [
        "button#index_login_button",
        "button[type='submit']",
        "input[type='submit']",
        "button.FlatButton--primary",
        ".login_btn",
    ]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn and btn.is_displayed():
                btn.click()
                return
        except Exception:
            continue
    from selenium.webdriver.common.keys import Keys

    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(Keys.RETURN)


def _login_vk(driver: WebDriver, login: str, password: str) -> Optional[str]:
    """Возвращает текст ошибки или код captcha/twofa."""
    wait = WebDriverWait(driver, 25)
    driver.get(settings.VK_SELENIUM_LOGIN_URL)
    time.sleep(1.0)
    susp = _page_text_suspicious(driver)
    if susp:
        return susp

    login_el, pass_el = _find_login_inputs(driver, wait)
    if not login_el or not pass_el:
        logger.warning("VK Selenium: login form fields not found")
        return "login_form"

    login_el.clear()
    login_el.send_keys(login)
    pass_el.clear()
    pass_el.send_keys(password)
    _submit_login(driver)

    time.sleep(2.5)
    susp = _page_text_suspicious(driver)
    if susp:
        return susp

    try:
        WebDriverWait(driver, 40).until(
            lambda d: _url_looks_logged_in(d.current_url or "")
        )
    except TimeoutException:
        logger.info("VK Selenium: timeout waiting for post-login URL, checking page...")

    body_lower = (driver.page_source or "").lower()
    if "неверный логин" in body_lower or "неверный пароль" in body_lower:
        return "credentials"
    if "заблокирован" in body_lower and "аккаунт" in body_lower:
        return "blocked"

    url = driver.current_url or ""
    if "login" in url.lower() or "act=auth" in url.lower():
        return "login_failed"

    return None


def _normalize_href(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    if s.startswith("//"):
        s = "https:" + s
    if s.startswith("/") and not s.startswith("//"):
        s = "https://vk.com" + s
    return s


def _collect_group_links(driver: WebDriver) -> List[Dict[str, Any]]:
    """Собирает уникальные сообщества со страницы групп."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    selectors = [s.strip() for s in settings.VK_SELENIUM_GROUP_LINK_SELECTORS.split(",") if s.strip()]
    elements: List[Any] = []
    for sel in selectors:
        try:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            if found:
                elements.extend(found)
        except Exception:
            continue
    if not elements:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='vk.com/club'], a[href*='vk.com/public']")
        except Exception:
            elements = []

    for el in elements:
        try:
            href = _normalize_href(el.get_attribute("href") or "")
            if not href or "vk.com" not in href:
                continue
            if _GROUP_HREF.search(href):
                m = _GROUP_HREF.search(href)
                gid = int(m.group(1)) if m else None
                key = f"id:{gid}"
                if key in seen:
                    continue
                seen.add(key)
                title = (el.text or "").strip()[:500] or None
                out.append({"id": gid, "name": title, "screen_name": None, "url": href})
                continue
            sm = _SCREEN_NAME.match(href)
            if sm:
                name = sm.group(1)
                if name in ("club", "public", "event", "im", "feed", "groups"):
                    continue
                key = f"sn:{name}"
                if key in seen:
                    continue
                seen.add(key)
                title = (el.text or "").strip()[:500] or None
                out.append({"id": None, "name": title, "screen_name": name, "url": href})
        except Exception:
            continue
    return out[:200]


def _scroll_page(driver: WebDriver, times: int, pause: float) -> None:
    for _ in range(max(1, times)):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except Exception:
            break
        time.sleep(pause)


def verify_vk_subscriptions_sync(
    login: str,
    password: str,
    user_id: Optional[int] = None,
) -> Tuple[bool, List[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Вход на vk.com и сбор списка сообществ со страницы групп (веб, не API).

    Returns:
        (ok, subscriptions, error_or_hint, diagnostic_s3_key) — последний: ключ PNG в S3 при ошибке Selenium.
    """
    login = (login or "").strip()
    password = (password or "").strip()
    if not login or not password:
        return False, [], "Укажите логин и пароль VK.", None

    driver: Optional[WebDriver] = None

    def _fail(msg: str) -> Tuple[bool, List[Dict[str, Any]], str, Optional[str]]:
        diag: Optional[str] = None
        if driver:
            diag = _save_diagnostic_screenshot(driver, user_id)
        return False, [], msg, diag

    try:
        driver = create_chrome_driver()
        err = _login_vk(driver, login, password)
        if err == "captcha":
            return _fail("Обнаружена капча. Войдите через OAuth или повторите позже.")
        if err == "twofa":
            return _fail("Требуется двухфакторная аутентификация. Используйте OAuth VK.")
        if err == "credentials":
            return _fail("Неверный логин или пароль.")
        if err == "blocked":
            return _fail("Аккаунт заблокирован или ограничен.")
        if err == "login_form":
            return _fail("Форма входа VK не найдена (смена вёрстки). Обновите селекторы или используйте OAuth.")
        if err == "login_failed":
            return _fail("Не удалось войти (проверьте логин/пароль или используйте OAuth).")

        groups_url = (settings.VK_SELENIUM_GROUPS_URL or "").strip() or "https://vk.com/groups"
        driver.get(groups_url)
        time.sleep(2.0)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        _scroll_page(driver, settings.VK_SELENIUM_SCROLL_TIMES, settings.VK_SELENIUM_SCROLL_PAUSE_SEC)

        subs = _collect_group_links(driver)
        hint = None
        if not subs:
            hint = (
                "Сообщества на странице не распознаны (пустой список или смена вёрстки). "
                "Вход мог пройти успешно — проверьте OAuth/API."
            )
        return True, subs, hint, None
    except Exception as e:
        logger.exception("VK Selenium probe failed: %s", e)
        diag: Optional[str] = None
        if driver:
            diag = _save_diagnostic_screenshot(driver, user_id)
        return False, [], f"Selenium: {e!s}"[:2000], diag
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


async def verify_vk_selenium_async(
    login: str,
    password: str,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Обёртка для FastAPI (async)."""
    import asyncio

    ok, subs, msg, diag_key = await asyncio.to_thread(
        verify_vk_subscriptions_sync, login, password, user_id
    )
    result: Dict[str, Any] = {"ok": ok, "subscriptions": subs, "source": "selenium_web"}
    if ok:
        if msg:
            result["message"] = msg
    else:
        result["error"] = msg or "Ошибка резервного входа VK"
        if diag_key:
            result["diagnostic_s3_key"] = diag_key
    return result
