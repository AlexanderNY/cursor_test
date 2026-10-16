"""Сохранение и восстановление Selenium-cookies Яндекс/Дзен."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Sequence

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

# Поля, которые Selenium add_cookie обычно принимает
_COOKIE_KEYS = ("name", "value", "domain", "path", "expiry", "secure", "httpOnly", "sameSite")

SESSION_EXPIRED_MESSAGE = (
    "Сессия Дзена истекла. Пройдите проверку авторизации ещё раз."
)


def filter_cookie_dict(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Оставляет только поля, пригодные для WebDriver.add_cookie."""
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    value = raw.get("value")
    if not name or value is None:
        return None
    out: Dict[str, Any] = {"name": str(name), "value": str(value)}
    for key in _COOKIE_KEYS:
        if key in ("name", "value"):
            continue
        if key not in raw or raw[key] is None:
            continue
        val = raw[key]
        if key == "expiry":
            try:
                out[key] = int(val)
            except (TypeError, ValueError):
                continue
        elif key in ("secure", "httpOnly"):
            out[key] = bool(val)
        else:
            out[key] = str(val)
    return out


def export_cookies(driver: Any) -> List[Dict[str, Any]]:
    """Снимает cookies с драйвера и нормализует поля."""
    try:
        raw_list = driver.get_cookies() or []
    except Exception as exc:
        logger.warning("export_cookies failed: %s", exc)
        return []
    out: List[Dict[str, Any]] = []
    for item in raw_list:
        filtered = filter_cookie_dict(item if isinstance(item, dict) else {})
        if filtered:
            out.append(filtered)
    return out


def cookies_nonempty(cookies: Any) -> bool:
    """True, если cookies — непустой список."""
    if not isinstance(cookies, list):
        return False
    return len(cookies) > 0


def classify_session_state(
    *,
    has_cookies: bool,
    looks_logged_in: Optional[bool] = None,
) -> str:
    """
    Чистая классификация для тестов и publish-гейта.
    Возвращает: missing | ok | expired | unknown
    """
    if not has_cookies:
        return "missing"
    if looks_logged_in is True:
        return "ok"
    if looks_logged_in is False:
        return "expired"
    return "unknown"


def is_publish_success_url(final_url: str) -> bool:
    """Успех публикации: страница dzen.ru, уже не редактор /article/new."""
    u = (final_url or "").strip().lower()
    if "dzen.ru" not in u:
        return False
    if "/article/new" in u:
        return False
    return True


def _cookie_domain(cookie: Dict[str, Any]) -> str:
    return (cookie.get("domain") or "").lower().lstrip(".")


def _is_dzen_domain(domain: str) -> bool:
    d = domain.lower().lstrip(".")
    return d == "dzen.ru" or d.endswith(".dzen.ru")


def _is_yandex_domain(domain: str) -> bool:
    d = domain.lower().lstrip(".")
    return (
        d == "yandex.ru"
        or d.endswith(".yandex.ru")
        or d == "ya.ru"
        or d.endswith(".ya.ru")
        or d == "yandex.com"
        or d.endswith(".yandex.com")
    )


def apply_cookies(driver: Any, cookies: Sequence[Dict[str, Any]]) -> None:
    """
    Восстанавливает cookies: сначала dzen.ru, затем ya.ru для .yandex.ru, снова dzen.ru.
    """
    normalized: List[Dict[str, Any]] = []
    for item in cookies:
        filtered = filter_cookie_dict(item if isinstance(item, dict) else {})
        if filtered:
            normalized.append(filtered)
    if not normalized:
        return

    dzen_cookies = [c for c in normalized if _is_dzen_domain(_cookie_domain(c))]
    yandex_cookies = [c for c in normalized if _is_yandex_domain(_cookie_domain(c))]
    other = [
        c
        for c in normalized
        if not _is_dzen_domain(_cookie_domain(c)) and not _is_yandex_domain(_cookie_domain(c))
    ]

    def _add_batch(batch: List[Dict[str, Any]]) -> None:
        for cookie in batch:
            try:
                driver.add_cookie(cookie)
            except Exception as exc:
                logger.debug("add_cookie %s failed: %s", cookie.get("name"), exc)

    try:
        driver.get("https://dzen.ru/")
        time.sleep(1.0)
        _add_batch(dzen_cookies)
        _add_batch(other)
    except Exception as exc:
        logger.warning("apply_cookies dzen base failed: %s", exc)

    if yandex_cookies:
        try:
            driver.get("https://ya.ru/")
            time.sleep(1.0)
            _add_batch(yandex_cookies)
        except Exception as exc:
            logger.warning("apply_cookies ya.ru failed: %s", exc)

    try:
        driver.get("https://dzen.ru/")
        time.sleep(2.0)
    except Exception as exc:
        logger.warning("apply_cookies final dzen navigate failed: %s", exc)


def session_looks_logged_in(driver: Any) -> bool:
    """Проверка, что после cookies пользователь на dzen.ru без экранов входа."""
    from .yandex_dzen_flow import _check_authenticated

    return bool(_check_authenticated(driver))


async def _ensure_session_columns(cur: Any) -> None:
    await cur.execute(
        """
        ALTER TABLE dzen_profiles
        ADD COLUMN IF NOT EXISTS yandex_session JSONB
        """
    )
    await cur.execute(
        """
        ALTER TABLE dzen_profiles
        ADD COLUMN IF NOT EXISTS yandex_session_saved_at TIMESTAMPTZ
        """
    )


async def save_yandex_session(user_id: int, cookies: Sequence[Dict[str, Any]]) -> bool:
    """Пишет cookies в dzen_profiles. Пустой список не сохраняет."""
    if not cookies_nonempty(list(cookies)):
        return False
    payload = json.dumps(list(cookies), ensure_ascii=False)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await _ensure_session_columns(cur)
            await cur.execute(
                """
                INSERT INTO dzen_profiles (user_id, yandex_session, yandex_session_saved_at, updated_at)
                VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    yandex_session = EXCLUDED.yandex_session,
                    yandex_session_saved_at = EXCLUDED.yandex_session_saved_at,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, payload),
            )
        return True
    except Exception:
        logger.exception("save_yandex_session failed user_id=%s", user_id)
        return False
    finally:
        await release_db_connection(conn)


async def clear_yandex_session(user_id: int) -> None:
    """Сбрасывает сохранённую сессию (cookies протухли)."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await _ensure_session_columns(cur)
            await cur.execute(
                """
                UPDATE dzen_profiles
                SET yandex_session = NULL,
                    yandex_session_saved_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """,
                (user_id,),
            )
    except Exception:
        logger.exception("clear_yandex_session failed user_id=%s", user_id)
    finally:
        await release_db_connection(conn)


def parse_session_cookies(raw: Any) -> List[Dict[str, Any]]:
    """Разбирает значение колонки yandex_session в список cookie-dict."""
    if raw is None:
        return []
    data = raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(data, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in data:
        filtered = filter_cookie_dict(item if isinstance(item, dict) else {})
        if filtered:
            out.append(filtered)
    return out
