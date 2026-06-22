"""Вход в аккаунт Яндекс через веб-интерфейс Passport."""

from __future__ import annotations

import logging
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from config import settings

logger = logging.getLogger(__name__)


class YandexAuthError(Exception):
    """Не удалось войти (капча, 2FA, неверный пароль и т.д.)."""


class PushCodeRequiredError(YandexAuthError):
    """Открыт экран ввода кода из пуш-уведомления (двухшаговый вход)."""


def _find_first(driver, selectors: list[tuple[str, str]]):
    for by, value in selectors:
        try:
            el = driver.find_element(by, value)
            if el:
                return el
        except Exception:
            continue
    return None


def dismiss_remind_later_popup(driver, timeout: float = 4.0) -> bool:
    """
    Закрывает всплывающее окно про биометрию: «Напомнить позже» / Remind me later.
    Returns True, если кнопка найдена и нажата.
    """
    from selenium.common.exceptions import StaleElementReferenceException
    from selenium.webdriver.support import expected_conditions as EC

    xpaths = [
        "//button[contains(normalize-space(.), 'Напомнить позже')]",
        "//a[contains(normalize-space(.), 'Напомнить позже')]",
        "//*[@role='button' and contains(normalize-space(.), 'Напомнить позже')]",
        (
            "//button[contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remind me later')]"
        ),
        (
            "//a[contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remind me later')]"
        ),
        "//*[@aria-label='Напомнить позже' or @aria-label='Remind me later']",
    ]
    short = min(max(1.0, timeout), 5.0)
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, short).until(EC.element_to_be_clickable((By.XPATH, xp)))
            if el.is_displayed():
                el.click()
                logger.info("Dismissed biometric popup: Remind me later")
                time.sleep(0.4)
                return True
        except (TimeoutException, StaleElementReferenceException):
            continue
        except Exception:
            continue
    return False


def dismiss_passport_overlays(driver) -> None:
    """Закрывает известные модальные окна Passport/ID, мешающие сценарию."""
    dismiss_remind_later_popup(driver, timeout=2.0)


def _safe_page_hint(driver) -> str:
    try:
        url = (driver.current_url or "")[:300]
        title = ""
        try:
            title = (driver.title or "")[:120]
        except Exception:
            pass
        parts = [f"url={url!r}"]
        if title:
            parts.append(f"title={title!r}")
        return "; ".join(parts)
    except Exception:
        return "url=н/д"


def _raise_login_field_timeout(driver, timeout_sec: int, cause: TimeoutException) -> None:
    hint = _safe_page_hint(driver)
    raise YandexAuthError(
        f"За {timeout_sec} с не найдено поле логина на странице Яндекс.Passport ({hint}). "
        "Проверьте доступность https://passport.yandex.ru из контейнера (DNS, файрвол), "
        "скорость сети и при смене вёрстки Яндекса — селекторы в dzen-bot/services/yandex_auth.py."
    ) from cause


def _raise_password_field_timeout(driver, timeout_sec: int, cause: TimeoutException) -> None:
    hint = _safe_page_hint(driver)
    raise YandexAuthError(
        f"За {timeout_sec} с не найдено поле пароля после ввода логина ({hint}). "
        "Возможна дополнительная страница (телефон, капча) или изменилась вёрстка Passport."
    ) from cause


def login_yandex_passport(driver, login: str, password: str) -> None:
    """
    Открывает Passport и вводит логин/пароль.
    Селекторы Яндекс периодически меняются — при сбоях обновить список ниже.
    """
    if not login or not password:
        raise YandexAuthError("Пустой логин или пароль")

    driver.get(settings.YANDEX_PASSPORT_URL)
    dismiss_passport_overlays(driver)
    login_timeout = max(25, int(settings.YANDEX_PASSPORT_LOGIN_TIMEOUT_SEC))
    wait = WebDriverWait(driver, login_timeout)

    login_selectors = [
        (By.ID, "passp-field-login"),
        (By.CSS_SELECTOR, "#passp-field-login"),
        (By.NAME, "login"),
        (By.CSS_SELECTOR, "input[type='text'][name='login']"),
        (By.CSS_SELECTOR, "input[name='login']"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input.input__control[type='text']"),
        (By.CSS_SELECTOR, "input[autocomplete='username']"),
    ]
    try:
        el_login = wait.until(lambda d: _find_first(d, login_selectors))
    except TimeoutException as e:
        _raise_login_field_timeout(driver, login_timeout, e)
    el_login.clear()
    el_login.send_keys(login)
    time.sleep(0.3)

    submit_login = _find_first(
        driver,
        [
            (By.ID, "passp:sign-in"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Войти') or contains(., 'Далее')]"),
        ],
    )
    if submit_login:
        submit_login.click()
    time.sleep(1.5)

    pwd_selectors = [
        (By.ID, "passp-field-passwd"),
        (By.CSS_SELECTOR, "#passp-field-passwd"),
        (By.NAME, "passwd"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
    ]
    pwd_timeout = max(20, int(settings.YANDEX_PASSPORT_PASSWORD_TIMEOUT_SEC))
    wait_pwd = WebDriverWait(driver, pwd_timeout)
    try:
        el_pwd = wait_pwd.until(lambda d: _find_first(d, pwd_selectors))
    except TimeoutException as e:
        _raise_password_field_timeout(driver, pwd_timeout, e)
    el_pwd.clear()
    el_pwd.send_keys(password)

    submit_pass = _find_first(
        driver,
        [
            (By.ID, "passp:sign-in"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(., 'Войти')]"),
        ],
    )
    if submit_pass:
        submit_pass.click()

    time.sleep(3.0)

    url = (driver.current_url or "").lower()
    page = (driver.page_source or "").lower()
    if "challenge" in url or "подтвердите" in page or "captcha" in page:
        raise YandexAuthError("Требуется дополнительная проверка (капча/SMS). Выполните вход вручную в профиле с персистентным браузером.")
    if "passport.yandex.ru/auth" in url and "session" not in url:
        # всё ещё на странице логина
        err_el = _find_first(
            driver,
            [
                (By.CSS_SELECTOR, ".passp-form-field__error"),
                (By.CSS_SELECTOR, "[role='alert']"),
            ],
        )
        msg = err_el.text.strip() if err_el is not None else "Не удалось войти (проверьте логин и пароль)."
        raise YandexAuthError(msg or "Ошибка авторизации Яндекс.")


def ensure_dzen_session(driver) -> None:
    """Открывает Дзен, чтобы проверить сессию после Passport."""
    driver.get("https://dzen.ru/")
    time.sleep(2.0)
    dismiss_passport_overlays(driver)
