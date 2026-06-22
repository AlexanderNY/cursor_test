"""
Вход через dzen.ru: кнопки «Войти» → «Войти через Яндекс ID» → при необходимости «Почта» и логин, пароль.
При экране пуша — возвращаем 'push' без raise (драйвер остаётся на стороне вызывающего кода).
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, List, Literal, Optional

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings

from .yandex_auth import (
    PushCodeRequiredError,
    YandexAuthError,
    _find_first,
    _safe_page_hint,
    dismiss_passport_overlays,
)

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

DzenFlowResult = Literal["ok", "push"]


def _lower_src(driver: "WebDriver", max_len: int = 400_000) -> str:
    try:
        return (driver.page_source or "")[:max_len].lower()
    except Exception:
        return ""


def _detect_captcha_block(driver: "WebDriver") -> bool:
    try:
        title = (driver.title or "").lower()
    except Exception:
        title = ""
    src = _lower_src(driver)
    markers = (
        "не робот",
        "не робот?",
        "smartcaptcha",
        "captcha by yandex",
        "подтвердите, что запросы",
        "подтвердите, что",
        "я не робот",
    )
    if any(m in src for m in markers):
        return True
    if "робот" in title and "?" in title:
        return True
    return False


def _wait_click(driver: "WebDriver", by, value: str, timeout: float) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        el.click()
        return True
    except Exception:
        return False


def _click_voyti_on_dzen(driver: "WebDriver", timeout: float) -> None:
    """Кнопка/ссылка «Войти» на главной Дзена."""
    time.sleep(1.0)
    # aria-label, затем кнопки/ссылки с текстом
    xpaths: List[str] = [
        "//*[@aria-label='Войти' or @aria-label='войти']",
        "//button[contains(., 'Войти') or contains(., 'войти')]",
        "//a[contains(., 'Войти') or contains(., 'войти')]",
        "//*[@role='button' and (contains(., 'Войти') or contains(., 'войти'))]",
    ]
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, min(timeout, 20)).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            el.click()
            return
        except (TimeoutException, Exception):
            continue
    raise YandexAuthError(
        "Не найдена кнопка «Войти» на dzen.ru. " + _safe_page_hint(driver)
    )


def _click_yandex_id_entry(driver: "WebDriver", timeout: float) -> None:
    time.sleep(0.8)
    candidates = [
        (By.XPATH, "//*[@aria-label='Войти через Яндекс ID' or @aria-label='Войти через яндекс id']"),
        (By.XPATH, "//*[contains(., 'Войти через Яндекс ID') or contains(., 'войти через яндекс id')]"),
    ]
    for by, val in candidates:
        try:
            el = WebDriverWait(driver, min(timeout, 25)).until(
                EC.element_to_be_clickable((by, val))
            )
            el.click()
            return
        except (TimeoutException, Exception):
            continue
    raise YandexAuthError(
        "Не найден элемент «Войти через Яндекс ID». " + _safe_page_hint(driver)
    )


def _if_voydite_s_id_use_pochta_and_login(
    driver: "WebDriver", login: str, short_wait: float
) -> bool:
    """Если на странице 'Войдите с ID' — жмём «Почта», вводим логин. Возвращает True если шаг выполнялся."""
    src = _lower_src(driver)
    if "войдите с id" not in src and "войдите с id" not in (driver.title or "").lower():
        return False
    for xp in (
        "//button[contains(., 'Почта') or contains(., 'почта')]",
        "//*[@role='tab' and (contains(., 'Почта') or contains(., 'почта'))]",
        "//*[contains(., 'Почта') and (self::button or self::a or self::div)]",
    ):
        if _wait_click(driver, By.XPATH, xp, 8.0):
            time.sleep(0.5)
            break
    login_selectors: List = [
        (By.CSS_SELECTOR, "input[aria-label='Логин или email']"),
        (By.CSS_SELECTOR, "input[aria-label='Логин или Email']"),
        (By.ID, "passp-field-login"),
        (By.CSS_SELECTOR, "input[name='login']"),
        (By.CSS_SELECTOR, "input[type='email']"),
    ]
    wait = WebDriverWait(driver, max(15, int(short_wait)))
    try:
        el = wait.until(lambda d: _find_first(d, login_selectors))
    except TimeoutException as e:
        raise YandexAuthError(
            "Не найдено поле логина (ожидалась вкладка Почта). " + _safe_page_hint(driver)
        ) from e
    el.clear()
    time.sleep(0.2)
    el.send_keys(login)
    time.sleep(0.2)
    el.send_keys(Keys.ENTER)
    time.sleep(1.2)
    return True


def _enter_login_and_submit(driver: "WebDriver", login: str, timeout: float) -> bool:
    login_selectors: List = [
        (By.CSS_SELECTOR, "input[aria-label='Логин или email']"),
        (By.CSS_SELECTOR, "input[aria-label='Логин или Email']"),
        (By.CSS_SELECTOR, "input[aria-label='Email or phone']"),
        (By.CSS_SELECTOR, "input[placeholder='Email or phone']"),
        (By.CSS_SELECTOR, "input[autocomplete='username']"),
        (By.ID, "passp-field-login"),
        (By.CSS_SELECTOR, "input[name='login']"),
        (By.CSS_SELECTOR, "input[name='identifier']"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[type='text']"),
        (By.XPATH, "//input[contains(@name,'login')]"),
        (By.XPATH, "//input[contains(@id,'login')]"),
    ]
    wait = WebDriverWait(driver, max(20, int(timeout)))
    try:
        el = wait.until(lambda d: _find_first(d, login_selectors))
    except TimeoutException:
        return False
    try:
        el.clear()
    except Exception:
        pass
    el.send_keys(login)
    el.send_keys(Keys.ENTER)
    time.sleep(1.2)
    return True


def _enter_password_and_submit(driver: "WebDriver", password: str, timeout: float) -> None:
    pwd_selectors: List = [
        (By.ID, "passp-field-passwd"),
        (By.CSS_SELECTOR, "input#passp-field-passwd"),
        (By.NAME, "passwd"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
    ]
    wait = WebDriverWait(driver, max(20, int(timeout)))
    last_stale: Optional[Exception] = None
    el = None
    for attempt in range(3):
        try:
            el = wait.until(lambda d: _find_first(d, pwd_selectors))
            el.clear()
            el.send_keys(password)
            time.sleep(0.2)
            sub = _find_first(
                driver,
                [
                    (By.ID, "passp:sign-in"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//button[contains(., 'Войти') or contains(., 'Sign in')]"),
                ],
            )
            if sub:
                sub.click()
            else:
                el.send_keys(Keys.ENTER)
            time.sleep(2.5)
            return
        except TimeoutException as e:
            if page_indicates_push_code(driver):
                raise PushCodeRequiredError(
                    "Требуется код из пуш-уведомления. " + _safe_page_hint(driver)
                ) from e
            raise YandexAuthError(
                "Не найдено поле пароля. " + _safe_page_hint(driver)
            ) from e
        except StaleElementReferenceException as e:
            last_stale = e
            if attempt >= 2:
                raise YandexAuthError(
                    "Страница сменилась при вводе пароля. Повторите проверку авторизации."
                ) from e
            time.sleep(0.5)


def page_indicates_push_code(driver: "WebDriver") -> bool:
    u = (driver.current_url or "").lower()
    url_markers = ("push-code", "/auth/push", "pwl-yandex/auth/push")
    if any(m in u for m in url_markers):
        return True

    t = (driver.title or "") + (driver.page_source or "")[:150000]
    tl = t.lower()
    text_markers = (
        "код из пуш",
        "введите код из пуш",
        "пуш-уведом",
        "push-уведом",
        "push notification",
        "enter the code",
        "confirmation code",
        "one-time code",
        "code from the app",
        "code from push",
    )
    if any(m in tl for m in text_markers):
        return True

    try:
        visible_pwd = [
            p for p in driver.find_elements(By.CSS_SELECTOR, "input[type='password']") if p.is_displayed()
        ]
        if visible_pwd:
            return False
        code_selectors = (
            "input[autocomplete='one-time-code']",
            "input[inputmode='numeric']",
            "input[type='tel']",
        )
        for sel in code_selectors:
            for inp in driver.find_elements(By.CSS_SELECTOR, sel):
                if inp.is_displayed():
                    return True
    except Exception:
        pass
    return False


def _check_authenticated(driver: "WebDriver") -> bool:
    u = (driver.current_url or "").lower()
    if "passport.yandex.ru" in u and "session" not in u and "auth" in u:
        return False
    body = _lower_src(driver)[:100000]
    if "войдите" in body and "passp" in body:
        return False
    if page_indicates_push_code(driver):
        return False
    if _detect_captcha_block(driver):
        return False
    return "dzen.ru" in u or "yandex" in u


def dzen_entry_run_until_push_or_ok(
    driver: "WebDriver", login: str, password: str
) -> DzenFlowResult:
    """
    Открывает dzen.ru, проходит сценарий входа.
    'push' — требуется ввод кода (драйвер остаётся открытым).
    'ok' — сессия для дальнейшей навигации (пароль введен, пуш-экрана нет).
    """
    if not (login and password):
        raise YandexAuthError("Пустой логин или пароль")

    base = (getattr(settings, "DZEN_ENTRY_BASE_URL", None) or "https://dzen.ru/").strip()
    short_w = 45.0

    driver.get(base)
    time.sleep(2.0)
    dismiss_passport_overlays(driver)
    if _detect_captcha_block(driver):
        raise YandexAuthError(
            "Обнаружена проверка SmartCaptcha/«не робот» на dzen.ru. "
            "Headless-режим и дата-центр IP часто блокируются. Попробуйте вручную, другой сеть или SELENIUM_HEADLESS=false (отладка)."
        )

    _click_voyti_on_dzen(driver, 25.0)
    time.sleep(1.0)
    dismiss_passport_overlays(driver)
    _click_yandex_id_entry(driver, 25.0)
    time.sleep(2.0)
    dismiss_passport_overlays(driver)

    if _detect_captcha_block(driver):
        raise YandexAuthError("Капча/антибот на этапе Яндекс ID. " + _safe_page_hint(driver))

    used_pochta = _if_voydite_s_id_use_pochta_and_login(driver, login, 25.0)
    if not used_pochta:
        if not _enter_login_and_submit(driver, login, 25.0):
            if page_indicates_push_code(driver):
                return "push"
            raise YandexAuthError(
                "Не найдено поле логина (в т.ч. Email or phone / passp-field-login). "
                + _safe_page_hint(driver)
            )

    dismiss_passport_overlays(driver)

    if page_indicates_push_code(driver):
        return "push"

    try:
        _enter_password_and_submit(
            driver, password, float(getattr(settings, "YANDEX_PASSPORT_PASSWORD_TIMEOUT_SEC", 40))
        )
    except PushCodeRequiredError:
        return "push"
    time.sleep(2.0)
    dismiss_passport_overlays(driver)

    if page_indicates_push_code(driver):
        return "push"

    if "passport.yandex.ru" in (driver.current_url or "").lower() and "auth" in (driver.current_url or ""):
        err = _find_first(
            driver,
            [(By.CSS_SELECTOR, ".passp-form-field__error"), (By.CSS_SELECTOR, "[role='alert']")],
        )
        msg = err.text.strip() if err else "Не удалось войти. Проверьте логин и пароль."
        raise YandexAuthError(msg or "Ошибка входа в Яндекс ID.")

    return "ok" if _check_authenticated(driver) or not page_indicates_push_code(driver) else "push"


def _find_push_code_input(driver: "WebDriver", timeout: float = 25.0):
    wait = WebDriverWait(driver, timeout)
    selectors: List = [
        (By.CSS_SELECTOR, "input[autocomplete='one-time-code']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
        (By.CSS_SELECTOR, "input[aria-label*='од']"),
        (By.XPATH, "//input[contains(@aria-label,'од')]"),
        (By.XPATH, "//input[contains(@aria-label,'code') or contains(@aria-label,'Code')]"),
    ]
    for by, val in selectors:
        try:
            el = wait.until(EC.element_to_be_clickable((by, val)))
            if el.is_displayed():
                return el
        except Exception:
            continue
    for inp in driver.find_elements(By.CSS_SELECTOR, "input"):
        try:
            if inp.is_displayed() and inp.is_enabled():
                return inp
        except StaleElementReferenceException:
            continue
    return None


def _click_submit_after_push_code(driver: "WebDriver") -> None:
    submit_selectors: List = [
        (By.XPATH, "//button[contains(., 'Продолж') or contains(., 'подтверд') or contains(., 'Continue') or contains(., 'Confirm')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(., 'Next') or contains(., 'Sign in')]"),
    ]
    for by, val in submit_selectors:
        btn = _find_first(driver, [(by, val)])
        if not btn:
            continue
        try:
            btn.click()
            return
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    fresh = _find_push_code_input(driver, 8.0)
    if fresh:
        fresh.send_keys(Keys.ENTER)


def _wait_push_code_page_settled(driver: "WebDriver", timeout: float = 25.0) -> None:
    def settled(d: "WebDriver") -> bool:
        u = (d.current_url or "").lower()
        if "push-code" not in u and not page_indicates_push_code(d):
            return True
        src = _lower_src(d)
        if any(m in src for m in ("неверн", "ошиб", "incorrect", "wrong", "invalid")):
            return True
        return False

    try:
        WebDriverWait(driver, timeout).until(settled)
    except TimeoutException:
        pass


def has_visible_password_field(driver: "WebDriver") -> bool:
    try:
        for pwd in driver.find_elements(By.CSS_SELECTOR, "input[type='password']"):
            if pwd.is_displayed():
                return True
    except StaleElementReferenceException:
        return False
    except Exception:
        return False
    return False


def complete_auth_after_push_code(driver: "WebDriver", password: str) -> None:
    """После пуш-кода Яндекс часто показывает экран пароля."""
    dismiss_passport_overlays(driver)
    if not has_visible_password_field(driver):
        return
    if not (password or "").strip():
        raise YandexAuthError("После кода требуется пароль, но он не задан в профиле Дзен.")
    _enter_password_and_submit(
        driver, password, float(getattr(settings, "YANDEX_PASSPORT_PASSWORD_TIMEOUT_SEC", 40))
    )
    time.sleep(2.0)
    dismiss_passport_overlays(driver)


def dzen_entry_submit_push_code(
    driver: "WebDriver", code: str
) -> None:
    c = (code or "").strip()
    if not c:
        raise YandexAuthError("Пустой код пуш-уведомления")

    dismiss_passport_overlays(driver)

    last_stale: Optional[Exception] = None
    for attempt in range(4):
        try:
            el = _find_push_code_input(driver)
            if not el:
                raise YandexAuthError("Поле для ввода кода не найдено. " + _safe_page_hint(driver))

            try:
                el.click()
            except StaleElementReferenceException as e:
                last_stale = e
                time.sleep(0.5)
                continue

            try:
                el.clear()
            except StaleElementReferenceException:
                driver.execute_script("arguments[0].value = '';", el)
            except Exception:
                driver.execute_script("arguments[0].value = '';", el)

            el.send_keys(c)
            time.sleep(0.35)
            _click_submit_after_push_code(driver)
            _wait_push_code_page_settled(driver)
            dismiss_passport_overlays(driver)
            break
        except StaleElementReferenceException as e:
            last_stale = e
            if attempt >= 3:
                raise YandexAuthError(
                    "Страница сменилась во время ввода кода. Нажмите «Проверить авторизацию» и повторите."
                    + " " + _safe_page_hint(driver)
                ) from e
            time.sleep(0.6)
    else:
        if last_stale:
            raise YandexAuthError(
                "Не удалось ввести код: элемент формы обновился (StaleElement). Повторите проверку."
            ) from last_stale

    if page_indicates_push_code(driver):
        s = _lower_src(driver)
        if any(m in s for m in ("неверн", "ошиб", "incorrect", "wrong", "invalid")):
            raise YandexAuthError("Код не принят. " + _safe_page_hint(driver))


def login_yandex_dzen_entry(driver: "WebDriver", login: str, password: str) -> None:
    """
    Полный сценарий dzen-входа без пуша (для publish/collect: если пуш — ошибка).
    """
    r = dzen_entry_run_until_push_or_ok(driver, login, password)
    if r == "push":
        raise YandexAuthError(
            "Требуется код из пуш-уведомления. Используйте проверку во вкладке «Авторизация» (двухшаговый вход) или войдите вручную."
        )


def yandex_auth_dispatch(driver: "WebDriver", login: str, password: str) -> None:
    """Точка входа для ботов: dzen-флоу или прямой Passport по config."""
    if getattr(settings, "USE_DZEN_ENTRY_AUTH", True):
        login_yandex_dzen_entry(driver, login, password)
    else:
        from .yandex_auth import login_yandex_passport

        login_yandex_passport(driver, login, password)
