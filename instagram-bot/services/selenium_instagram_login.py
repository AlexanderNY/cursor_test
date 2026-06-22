"""Авторизация в Instagram через Selenium: главная страница, RU/EN селекторы."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from services.selenium_driver import create_chrome_driver
from services.selenium_diag_storage import try_capture_and_upload_diag
from services.selenium_selectors import (
    LOGIN_ARIA_LABELS,
    LOGIN_BUTTON_TEXT_SUBSTRINGS,
    PASSWORD_LABEL_SUBSTRINGS,
    USERNAME_LABEL_SUBSTRINGS,
)

logger = logging.getLogger(__name__)

START_URL = "https://www.instagram.com/"


@dataclass
class SeleniumInstagramLoginResult:
    ok: bool
    status: str
    message: str
    cookie_dict: Optional[Dict[str, str]] = None
    diagnostic_s3_key: Optional[str] = None
    # base64 PNG без префикса data:, для <img src="data:image/png;base64,...">
    diagnostic_image_base64: Optional[str] = None


def _fail_with_diag(
    driver: Any,
    status: str,
    message: str,
    reason_slug: str,
) -> SeleniumInstagramLoginResult:
    s3_key, b64 = try_capture_and_upload_diag(driver, reason_slug)
    return SeleniumInstagramLoginResult(
        ok=False,
        status=status,
        message=message,
        diagnostic_s3_key=s3_key,
        diagnostic_image_base64=b64,
    )


def _find_visible_first(driver: Any, by: str, value: str) -> List[Any]:
    out = []
    for el in driver.find_elements(by, value):
        try:
            if el.is_displayed():
                out.append(el)
        except Exception:
            continue
    return out


def _fill_username_field(driver: Any, short_wait: WebDriverWait, username: str) -> bool:
    for name in ("email", "username"):
        try:
            el = short_wait.until(EC.element_to_be_clickable((By.NAME, name)))
            el.clear()
            el.send_keys(username)
            return True
        except Exception:
            continue

    for sub in USERNAME_LABEL_SUBSTRINGS:
        try:
            xp = f"//*[contains(., '{sub}')]"
            for node in _find_visible_first(driver, By.XPATH, xp):
                try:
                    node.click()
                    time.sleep(0.35)
                    for by, val in (
                        (By.NAME, "email"),
                        (By.NAME, "username"),
                        (By.CSS_SELECTOR, "input[type='email']"),
                        (By.CSS_SELECTOR, "input[type='text']"),
                    ):
                        for inp in _find_visible_first(driver, by, val):
                            try:
                                inp.clear()
                                inp.send_keys(username)
                                return True
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception:
            continue
    return False


def _fill_password_field(driver: Any, short_wait: WebDriverWait, password: str) -> bool:
    for name in ("pass", "password"):
        try:
            el = short_wait.until(EC.element_to_be_clickable((By.NAME, name)))
            el.clear()
            el.send_keys(password)
            return True
        except Exception:
            continue

    for sub in PASSWORD_LABEL_SUBSTRINGS:
        if sub == "Пароль":
            xps = [
                "//label[contains(.,'Пароль')]",
                "//span[contains(.,'Пароль')]",
                f"//*[contains(., '{sub}')]",
            ]
        else:
            xps = [f"//*[contains(., '{sub}')]" for sub in (sub,)]

        for xp in xps:
            try:
                for node in _find_visible_first(driver, By.XPATH, xp):
                    if sub == "Пароль" and node.tag_name.lower() in ("div", "form", "body"):
                        continue
                    try:
                        node.click()
                        time.sleep(0.3)
                    except Exception:
                        continue
                    for inp in _find_visible_first(driver, By.CSS_SELECTOR, "input[type='password']"):
                        try:
                            inp.clear()
                            inp.send_keys(password)
                            return True
                        except Exception:
                            continue
            except Exception:
                continue

    for inp in _find_visible_first(driver, By.CSS_SELECTOR, "input[type='password']"):
        try:
            inp.clear()
            inp.send_keys(password)
            return True
        except Exception:
            continue
    return False


def _click_login_button(driver: Any, short_wait: WebDriverWait) -> bool:
    for aria in LOGIN_ARIA_LABELS:
        if not (aria and str(aria).strip()):
            continue
        try:
            for el in _find_visible_first(
                driver,
                By.XPATH,
                f"//*[@aria-label='{aria}']",
            ):
                try:
                    el.click()
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    for sub in LOGIN_BUTTON_TEXT_SUBSTRINGS:
        xp = (
            f"//button[contains(normalize-space(.), '{sub}')] | "
            f"//div[@role='button'][contains(normalize-space(.), '{sub}')] | "
            f"//a[contains(normalize-space(.), '{sub}')]"
        )
        try:
            for el in _find_visible_first(driver, By.XPATH, xp):
                try:
                    el.click()
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def _instagram_cookie_dict_from_driver(driver: Any) -> Dict[str, str]:
    raw = driver.get_cookies()
    out: Dict[str, str] = {}
    for c in raw:
        domain = (c.get("domain") or "").lower()
        if "instagram.com" not in domain:
            continue
        name = c.get("name")
        if name:
            out[str(name)] = str(c.get("value", ""))
    return out


def _dismiss_common_modals(driver: Any) -> None:
    for _ in range(3):
        for xpath in (
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Not now')]",
        ):
            try:
                for el in driver.find_elements(By.XPATH, xpath)[:2]:
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.4)
            except Exception:
                pass
        time.sleep(0.25)


def attempt_instagram_login_via_selenium(username: str, password: str) -> SeleniumInstagramLoginResult:
    """
    Старт с главной instagram.com, поиск полей по name и по тексту (RU/EN), вход.
    """
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return SeleniumInstagramLoginResult(
            ok=False,
            status="error",
            message="username_and_password_required",
        )

    timeout = max(30, int(getattr(settings, "SELENIUM_INSTAGRAM_LOGIN_TIMEOUT_SEC", 120)))
    wait_timeout = min(30, max(10, timeout // 2))
    driver = None
    try:
        driver = create_chrome_driver()
        driver.get(START_URL)
        time.sleep(1.2)

        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            pass

        short_wait = WebDriverWait(driver, wait_timeout)
        if not _fill_username_field(driver, short_wait, username):
            return _fail_with_diag(driver, "failed", "username_field_not_found", "username_not_found")
        if not _fill_password_field(driver, short_wait, password):
            return _fail_with_diag(driver, "failed", "password_field_not_found", "password_not_found")
        if not _click_login_button(driver, short_wait):
            return _fail_with_diag(driver, "failed", "login_button_not_found", "login_button_not_found")

        deadline = time.monotonic() + float(timeout)
        while time.monotonic() < deadline:
            url = (driver.current_url or "").lower()
            if "challenge" in url or "checkpoint" in url:
                return _fail_with_diag(
                    driver,
                    "challenge",
                    "instagram_challenge_or_checkpoint_requires_manual_step",
                    "challenge_in_loop",
                )
            cookies = _instagram_cookie_dict_from_driver(driver)
            if cookies.get("sessionid") and cookies.get("ds_user_id"):
                _dismiss_common_modals(driver)
                cookies = _instagram_cookie_dict_from_driver(driver)
                return SeleniumInstagramLoginResult(
                    ok=True,
                    status="success",
                    message="web_login_ok",
                    cookie_dict=cookies,
                )
            time.sleep(1.0)

        url = (driver.current_url or "").lower()
        if "challenge" in url or "checkpoint" in url:
            return _fail_with_diag(
                driver,
                "challenge",
                "instagram_challenge_or_checkpoint_requires_manual_step",
                "challenge_after_wait",
            )
        return _fail_with_diag(
            driver,
            "failed",
            "timeout_waiting_for_session_cookies",
            "timeout_session_cookies",
        )
    except Exception as e:
        logger.exception("Selenium Instagram login error: %s", e)
        s3_key, b64 = (None, None)
        if driver is not None:
            s3_key, b64 = try_capture_and_upload_diag(driver, "exception")
        return SeleniumInstagramLoginResult(
            ok=False,
            status="error",
            message=f"{type(e).__name__}: {e}",
            diagnostic_s3_key=s3_key,
            diagnostic_image_base64=b64,
        )
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                logger.warning("driver.quit(): %s", e)
