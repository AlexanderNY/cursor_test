"""Проверка входа Яндекс и чтение списка подписок Дзена через Selenium."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from database import get_db_connection, release_db_connection

from .selenium_diag import capture_diag_for_ui, capture_selenium_error_to_s3
from .selenium_driver import create_chrome_driver
from .selenium_errors import format_selenium_exception
from .pending_yandex_session import get_session, pop_and_quit, put_session
from .yandex_auth import PushCodeRequiredError, YandexAuthError, ensure_dzen_session, dismiss_passport_overlays
from .yandex_dzen_flow import (
    complete_auth_after_push_code,
    dzen_entry_run_until_push_or_ok,
    dzen_entry_submit_push_code,
    page_indicates_push_code,
    yandex_auth_dispatch,
)

logger = logging.getLogger(__name__)

_PUSH_MESSAGE = "Введите код из пуш-уведомления Яндекса."


def _diag_url(driver: Optional[WebDriver], label: str, user_id: Optional[int]) -> Optional[str]:
    return capture_diag_for_ui(driver, label, user_id=user_id).get("diag_image_url")


def _push_code_start_response(driver: WebDriver, user_id: int, label: str) -> Dict[str, Any]:
    diag = capture_diag_for_ui(driver, label, user_id=user_id)
    put_session(user_id, driver)
    return {
        "ok": True,
        "need_push_code": True,
        "message": _PUSH_MESSAGE,
        "subscriptions": [],
        "error": None,
        "diag_image_url": diag.get("diag_image_url"),
    }

# Ссылки на каналы/паблишеров в ленте подписок
_HREF_CHANNEL = re.compile(
    r"https?://(?:www\.)?dzen\.ru/(?:id/[^/?#]+|media/id/[^/?#]+|profile/[^/?#]+)(?:/|$|\?)",
    re.IGNORECASE,
)


def _normalize_href(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    if s.startswith("//"):
        s = "https:" + s
    if s.startswith("/"):
        s = "https://dzen.ru" + s
    return s


def _link_title(el) -> str:
    try:
        t = (el.text or "").strip()
        if t:
            return t[:500]
        t2 = el.get_attribute("title") or el.get_attribute("aria-label") or ""
        return (t2 or "").strip()[:500]
    except Exception:
        return ""


def _collect_subscription_links(driver: WebDriver) -> List[Dict[str, str]]:
    """Собирает уникальные ссылки на каналы со страницы подписок."""
    seen: set[str] = set()
    out: List[Dict[str, str]] = []

    selectors = [s.strip() for s in settings.DZEN_SUBSCRIPTIONS_LINK_SELECTORS.split(",") if s.strip()]
    elements: List[object] = []
    for sel in selectors:
        try:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            if found:
                elements.extend(found)
        except Exception:
            continue

    if not elements:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='dzen.ru']")
        except Exception:
            elements = []

    for el in elements:
        try:
            href = el.get_attribute("href") or ""
            href = _normalize_href(href)
            if not href or "passport.yandex" in href:
                continue
            if not _HREF_CHANNEL.search(href):
                continue
            parsed = urlparse(href)
            path = (parsed.path or "").rstrip("/")
            key = f"{parsed.netloc}{path}"
            if key in seen:
                continue
            seen.add(key)
            title = _link_title(el) or path.split("/")[-1] or href
            out.append({"title": title, "url": href})
        except Exception:
            continue

    return out


def _scroll_page(driver: WebDriver, times: int = 3) -> None:
    for _ in range(max(1, times)):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(float(settings.DZEN_SUBSCRIPTIONS_SCROLL_PAUSE_SEC))
        except Exception:
            break


def run_subscriptions_collection_driver(
    driver: WebDriver, user_id: Optional[int]
) -> Tuple[List[Dict[str, str]], Optional[str]]:
    ensure_dzen_session(driver)
    url = (settings.DZEN_SUBSCRIPTIONS_URL or "").strip() or "https://dzen.ru/subscriptions"
    driver.get(url)
    time.sleep(2.0)
    dismiss_passport_overlays(driver)
    wait_sec = max(15, int(settings.DZEN_SUBSCRIPTIONS_WAIT_SEC))
    WebDriverWait(driver, wait_sec).until(lambda d: d.find_element(By.TAG_NAME, "body"))
    cur = (driver.current_url or "").lower()
    if "passport.yandex" in cur and "session" not in cur:
        return [], "Редирект на Passport: сессия Дзена не подтверждена"
    time.sleep(2.0)
    _scroll_page(driver, settings.DZEN_SUBSCRIPTIONS_SCROLL_TIMES)
    subs = _collect_subscription_links(driver)
    if not subs:
        time.sleep(3.0)
        _scroll_page(driver, 2)
        subs = _collect_subscription_links(driver)
    warn: Optional[str] = None
    if not subs:
        warn = (
            "Вход выполнен, но подписки на странице не распознаны "
            "(пустой список или изменилась вёрстка Дзена)."
        )
        logger.info("Dzen subscriptions: 0 items (user_id=%s)", user_id)
    return subs, warn


def verify_subscriptions_sync(
    login: str, password: str, user_id: Optional[int] = None
) -> Tuple[bool, List[Dict[str, str]], Optional[str]]:
    """
    Один заход: вход (dzen-флоу / passport) + подписки. При пуш-экране — YandexAuthError.
    """
    login = (login or "").strip()
    password = (password or "").strip()
    if not login or not password:
        return False, [], "Не заданы логин или пароль в профиле Дзен"

    driver: Optional[WebDriver] = None
    try:
        driver = create_chrome_driver()
        yandex_auth_dispatch(driver, login, password)
        subs, wmsg = run_subscriptions_collection_driver(driver, user_id)
        if wmsg and "не подтверждена" in wmsg:
            return False, [], wmsg
        return True, subs, wmsg
    except YandexAuthError as e:
        logger.warning("Dzen subscriptions probe: %s", e)
        capture_selenium_error_to_s3(driver, "subscriptions_probe_yandex_auth", user_id=user_id)
        return False, [], str(e)
    except Exception as e:
        friendly = format_selenium_exception(e)
        capture_selenium_error_to_s3(driver, "subscriptions_probe_exception", user_id=user_id)
        logger.exception("Dzen subscriptions probe failed: %s", friendly)
        return False, [], friendly
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def verify_yandex_start_sync(user_id: int, login: str, password: str) -> Dict[str, Any]:
    """Dzen-вход с возможностью паузы на пуш. При пуше WebDriver в pending (не quit)."""
    pop_and_quit(user_id)
    login = (login or "").strip()
    password = (password or "").strip()
    if not login or not password:
        return {
            "ok": False,
            "need_push_code": False,
            "subscriptions": [],
            "error": "Не заданы логин или пароль в профиле Дзен",
            "message": None,
            "diag_image_url": None,
        }
    driver: Optional[WebDriver] = None
    keep_driver = False
    try:
        driver = create_chrome_driver()
        rflow = dzen_entry_run_until_push_or_ok(driver, login, password)
        if rflow == "push":
            res = _push_code_start_response(driver, user_id, "verify_yandex_start_push")
            keep_driver = True
            driver = None
            return res
        subs, wmsg = run_subscriptions_collection_driver(driver, user_id)
        res: Dict[str, Any] = {
            "ok": True,
            "need_push_code": False,
            "subscriptions": subs,
            "message": wmsg,
            "error": None,
            "diag_image_url": None,
        }
        if wmsg and "не подтверждена" in wmsg:
            res["ok"] = False
            res["error"] = wmsg
        return res
    except PushCodeRequiredError:
        if not driver:
            return {
                "ok": True,
                "need_push_code": True,
                "message": _PUSH_MESSAGE,
                "subscriptions": [],
                "error": None,
                "diag_image_url": None,
            }
        res = _push_code_start_response(driver, user_id, "verify_yandex_start_push_exc")
        keep_driver = True
        driver = None
        return res
    except YandexAuthError as e:
        du = _diag_url(driver, "verify_yandex_start_auth_err", user_id)
        return {
            "ok": False,
            "need_push_code": False,
            "subscriptions": [],
            "error": str(e),
            "message": None,
            "diag_image_url": du,
        }
    except Exception as e:
        friendly = format_selenium_exception(e)
        logger.exception("verify_yandex_start: %s", friendly)
        durl = _diag_url(driver, "verify_yandex_start_exc", user_id)
        return {
            "ok": False,
            "need_push_code": False,
            "subscriptions": [],
            "error": friendly,
            "message": None,
            "diag_image_url": durl,
        }
    finally:
        if driver and not keep_driver:
            try:
                driver.quit()
            except Exception:
                pass


def verify_yandex_push_code_sync(
    user_id: int, code: str, password: Optional[str] = None
) -> Dict[str, Any]:
    s = get_session(user_id)
    if not s:
        return {
            "ok": False,
            "need_push_code": True,
            "subscriptions": [],
            "error": "Сессия ожидания пуша не найдена. Нажмите «Проверить» снова.",
            "message": None,
            "diag_image_url": None,
        }
    with s.op_lock:
        driver = s.driver
        try:
            dzen_entry_submit_push_code(driver, code)
            complete_auth_after_push_code(driver, password or "")
            if page_indicates_push_code(driver):
                du = _diag_url(driver, "push_code_retry", user_id)
                return {
                    "ok": False,
                    "need_push_code": True,
                    "subscriptions": [],
                    "error": "Сценарий по-прежнему ожидает код. Повторите ввод.",
                    "message": None,
                    "diag_image_url": du,
                }
            subs, wmsg = run_subscriptions_collection_driver(driver, user_id)
            pop_and_quit(user_id)
            return {
                "ok": True,
                "need_push_code": False,
                "subscriptions": subs,
                "message": wmsg,
                "error": None,
                "diag_image_url": None,
            }
        except StaleElementReferenceException as e:
            friendly = (
                "Страница Яндекса обновилась во время входа (StaleElement). "
                "Нажмите «Проверить авторизацию» и введите код снова."
            )
            du = _diag_url(driver, "push_code_stale", user_id)
            logger.warning("verify_yandex_push_code stale: %s", e)
            return {
                "ok": False,
                "need_push_code": True,
                "subscriptions": [],
                "error": friendly,
                "message": None,
                "diag_image_url": du,
            }
        except YandexAuthError as e:
            du = _diag_url(driver, "push_code_error", user_id)
            return {
                "ok": False,
                "need_push_code": True,
                "subscriptions": [],
                "error": str(e),
                "message": None,
                "diag_image_url": du,
            }
        except Exception as e:
            friendly = format_selenium_exception(e)
            du = _diag_url(driver, "push_code_exception", user_id)
            return {
                "ok": False,
                "need_push_code": True,
                "subscriptions": [],
                "error": friendly,
                "message": None,
                "diag_image_url": du,
            }


def verify_yandex_pending_diag_sync(user_id: int) -> Dict[str, Any]:
    """Снимок текущего экрана pending WebDriver (для UI при таймауте push-code)."""
    s = get_session(user_id)
    if not s:
        return {"diag_image_url": None, "error": "Нет активной сессии Selenium."}
    acquired = s.op_lock.acquire(blocking=False)
    if not acquired:
        return {
            "diag_image_url": None,
            "error": "Сессия занята проверкой. Повторите обновление скрина через несколько секунд.",
        }
    try:
        return {"diag_image_url": _diag_url(s.driver, "pending_diag_refresh", user_id)}
    finally:
        s.op_lock.release()


async def fetch_yandex_credentials(user_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Читает логин и пароль из БД (как в publisher)."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT yandex_login, yandex_password
                FROM dzen_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None, None
            login = (row[0] or "").strip() if row[0] else None
            password = (row[1] or "").strip() if row[1] else None
            return login, password
    finally:
        await release_db_connection(conn)


async def set_last_auth_error(user_id: int, message: Optional[str]) -> None:
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


async def verify_yandex_start_for_user(user_id: int) -> Dict[str, Any]:
    """Старт проверки: dzen-вход, при необходимости пуш, иначе подписки."""
    import asyncio

    login, password = await fetch_yandex_credentials(user_id)
    if not login or not password:
        err = "Сохраните логин и пароль Яндекса во вкладке «Авторизация» (профиль Дзен)."
        await set_last_auth_error(user_id, err)
        return {
            "ok": False,
            "need_push_code": False,
            "subscriptions": [],
            "error": err,
            "message": None,
            "diag_image_url": None,
        }

    d = await asyncio.to_thread(verify_yandex_start_sync, user_id, login, password)
    if d.get("ok") and d.get("need_push_code"):
        await set_last_auth_error(user_id, None)
    elif d.get("error"):
        await set_last_auth_error(user_id, str(d["error"])[:2000])
    else:
        await set_last_auth_error(user_id, None)
    return d


async def verify_yandex_pending_diag_for_user(user_id: int) -> Dict[str, Any]:
    import asyncio

    return await asyncio.to_thread(verify_yandex_pending_diag_sync, user_id)


async def verify_yandex_push_for_user(user_id: int, code: str) -> Dict[str, Any]:
    import asyncio

    _, password = await fetch_yandex_credentials(user_id)
    d = await asyncio.to_thread(verify_yandex_push_code_sync, user_id, code, password)
    if d.get("ok") and not d.get("error"):
        await set_last_auth_error(user_id, None)
    elif d.get("error"):
        await set_last_auth_error(user_id, str(d["error"])[:2000])
    return d
