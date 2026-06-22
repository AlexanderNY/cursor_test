"""
Синхронный сценарий веб-входа в Instagram (instagram.com) для диагностики.
Не извлекает Graph API token и не заменяет OAuth для Threads API.

Реалистичные ограничения: лендинг/challenge/cookies, A/B и локализация (RU/EN)
могут отличаться — в коде есть fallback; это не гарантирует 24/7-устойчивость
и не заменяет OAuth Graph API.

Пароль не пишется в логи. При сбоях — diagnostic_png для S3 (ключ с подстрокой diag).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, Tuple

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
import services.instagram_selenium_helpers as ig

logger = logging.getLogger(__name__)


def _find_first(driver: WebDriver, selectors: list[tuple[str, str]]):
    for by, value in selectors:
        try:
            el = driver.find_element(by, value)
            if el and el.is_displayed():
                return el
        except WebDriverException:
            continue
    return None


def _capture_diag_png(driver: Optional[WebDriver]) -> Optional[bytes]:
    if not driver:
        return None
    try:
        return driver.get_screenshot_as_png()
    except Exception:
        logger.warning("Instagram selenium: get_screenshot_as_png failed", exc_info=True)
        return None


def _detect_instagram_state(driver: WebDriver) -> tuple[str, str]:
    """
    Успех / challenge / 2FA / бан / ошибка по URL и (частично) странице.
    Не ориентируемся на facebook.com.
    """
    url = (driver.current_url or "").lower()
    src = (driver.page_source or "").lower()[:20000]

    if "suspended" in url or "suspended" in src:
        return "failed", "Аккаунт в статусе suspended. Требуется ручной разбор в Instagram."
    if "challenge" in url or "checkpoint" in url or "checkpoint" in src:
        return (
            "challenge_required",
            "Instagram запросил проверку (challenge / checkpoint). Завершите вход вручную в браузере.",
        )
    if "two_factor" in url or "two factor" in src or "2fa" in src:
        return (
            "challenge_required",
            "Требуется двухфакторная аутентификация. Выполните шаг вручную.",
        )
    if "consent" in url or "accounts/confirm" in url:
        return "challenge_required", "Требуется подтверждение или согласие в Instagram. Завершите вручную."

    if "accounts/login" in url and ("error" in src or "попроб" in src or "incorrect" in src):
        return "failed", "Не удалось войти (проверьте логин и пароль)."

    if "accounts/onetap" in url:
        return (
            "completed_unverified",
            "Сессия дошла до onetap. Для публикации через API по-прежнему нужен «Connect with Threads» (OAuth), не веб-логин.",
        )
    if "instagram.com" in url and "login" not in url and "challenge" not in url and "suspended" not in url:
        return (
            "completed_unverified",
            "Браузер покинул страницу логина (Instagram). Для публикации через API по-прежнему нужен «Connect with Threads» (OAuth), не веб-логин.",
        )
    return (
        "failed",
        "Не удалось определить результат входа (таймаут, капча или смена вёрстки Instagram).",
    )


def run_meta_web_login(
    username: str,
    password: str,
    user_id: int,
    session_id: int,
) -> dict[str, Any]:
    """
    Пытается ввести учётные данные в веб-форму Instagram.
    """
    _ = user_id, session_id
    if not username or not password:
        return {"status": "failed", "message": "Пустой логин или пароль", "diagnostic_png": None}

    from services.selenium_driver import create_chrome_driver

    driver: Optional[WebDriver] = None
    start_url = settings.INSTAGRAM_WEB_LOGIN_URL

    def finish(
        status: str,
        message: str,
        *,
        diag: bool = False,
    ) -> dict[str, Any]:
        png: Optional[bytes] = None
        if diag and driver:
            png = _capture_diag_png(driver)
        return {"status": status, "message": message, "diagnostic_png": png}

    try:
        driver = create_chrome_driver()
        driver.get(start_url)
        time.sleep(1.5)
        wait = WebDriverWait(driver, 25)

        if not ig.find_email_input_and_fill(driver, username, wait):
            logger.warning("Instagram selenium: email/username field not found")
            return finish(
                "failed",
                "Не найдено поле логина (проверьте локализацию или вёрстку Instagram).",
                diag=True,
            )
        time.sleep(0.5)

        if not ig.find_password_input_and_fill(driver, password, wait):
            return finish("failed", "Не найдено поле пароля.", diag=True)
        time.sleep(0.4)

        clicked = ig.find_and_click_login_button(driver, wait)
        if not clicked:
            el_pass = _find_first(
                driver,
                [
                    (By.NAME, "pass"),
                    (By.CSS_SELECTOR, "input[name='pass']"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                ],
            )
            if el_pass:
                el_pass.send_keys(Keys.RETURN)
            else:
                return finish("failed", "Не найдена кнопка входа.", diag=True)
        time.sleep(4.0)
        code, msg = _detect_instagram_state(driver)
        if code in ("failed", "challenge_required"):
            png = _capture_diag_png(driver)
            return {"status": code, "message": msg, "diagnostic_png": png}
        return {"status": code, "message": msg, "diagnostic_png": None}

    except TimeoutException as e:
        logger.warning("Instagram selenium timeout: %s", e)
        png = _capture_diag_png(driver)
        return {
            "status": "failed",
            "message": "Таймаут при загрузке или вводе (страница Instagram могла измениться).",
            "diagnostic_png": png,
        }
    except WebDriverException as e:
        logger.warning("Instagram selenium webdriver error: %s", e)
        png = _capture_diag_png(driver)
        return {
            "status": "failed",
            "message": "Ошибка браузера при входе. Проверьте Chrome/Chromium в контейнере.",
            "diagnostic_png": png,
        }
    finally:
        if driver:
            try:
                driver.quit()
            except WebDriverException:
                pass
