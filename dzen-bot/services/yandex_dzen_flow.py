"""
Вход через dzen.ru: «Войти» → popup → «Войти через Яндекс ID» → телефон → SMS-код.
Опционально: имя/фамилия, выбор аккаунта, «Напомнить позже» (биометрия).
При экране кода — возвращаем 'push' без raise (драйвер остаётся у вызывающего).
"""

from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Callable, List, Literal, Optional

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings

from .phone_utils import PhoneNormalizeError, normalize_ru_phone
from .yandex_auth import (
    PushCodeRequiredError,
    YandexAuthError,
    _find_first,
    _safe_page_hint,
    dismiss_passport_overlays,
    dismiss_remind_later_popup,
)

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

DzenFlowResult = Literal["ok", "push"]

_POST_CODE_TIMEOUT_SEC = 60.0
_OPTIONAL_STEP_WAIT = 3.0

__all__ = [
    "DzenFlowResult",
    "normalize_ru_phone",
    "page_indicates_push_code",
    "complete_auth_after_push_code",
    "complete_auth_after_code",
    "dzen_entry_run_until_push_or_ok",
    "dzen_entry_submit_push_code",
    "login_yandex_dzen_entry",
    "yandex_auth_dispatch",
    "has_visible_password_field",
]


def _phone_or_raise(raw: str) -> str:
    try:
        return normalize_ru_phone(raw)
    except PhoneNormalizeError as e:
        raise YandexAuthError(str(e)) from e


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
    """Кнопка «Войти» на главной Дзена: data-testid, затем aria-label."""
    time.sleep(1.0)
    candidates = [
        (By.CSS_SELECTOR, "[data-testid='login-button']"),
        (By.CSS_SELECTOR, "button[aria-label='Войти']"),
        (By.CSS_SELECTOR, "[aria-label='Войти']"),
        (By.XPATH, "//*[@aria-label='Войти' or @aria-label='войти']"),
        (By.XPATH, "//button[contains(., 'Войти') or contains(., 'войти')]"),
    ]
    for by, val in candidates:
        try:
            el = WebDriverWait(driver, min(timeout, 20)).until(
                EC.element_to_be_clickable((by, val))
            )
            el.click()
            return
        except (TimeoutException, Exception):
            continue
    raise YandexAuthError(
        "Не найдена кнопка «Войти» на dzen.ru. " + _safe_page_hint(driver)
    )


def _wait_login_popup(driver: "WebDriver", timeout: float) -> None:
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='popup-base']"))
        )
    except TimeoutException as e:
        raise YandexAuthError(
            "Не появился popup авторизации (popup-base). " + _safe_page_hint(driver)
        ) from e


def _click_yandex_id_entry(driver: "WebDriver", timeout: float) -> None:
    time.sleep(0.5)
    candidates = [
        (By.CSS_SELECTOR, "[aria-label='Войти через Яндекс ID']"),
        (By.XPATH, "//*[@aria-label='Войти через Яндекс ID' or @aria-label='Войти через яндекс id']"),
        (By.XPATH, "//a[contains(., 'Войти через Яндекс ID') or contains(., 'войти через яндекс id')]"),
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


def _click_phone_tab(driver: "WebDriver", timeout: float = 15.0) -> bool:
    """Переключает сегмент на «Телефон». True если кликнули."""
    candidates = [
        (By.CSS_SELECTOR, "[data-testid='add-user-phone-option']"),
        (By.XPATH, "//span[@data-testid='label' and normalize-space()='Телефон']"),
        (By.XPATH, "//label[@data-testid='option' and contains(., 'Телефон')]"),
        (By.XPATH, "//*[normalize-space()='Телефон' and (self::span or self::label or self::button)]"),
    ]
    for by, val in candidates:
        if _wait_click(driver, by, val, min(timeout, 8.0)):
            time.sleep(0.4)
            return True
    return False


def _enter_phone_and_submit(driver: "WebDriver", phone: str, timeout: float) -> None:
    phone_digits = _phone_or_raise(phone)
    selectors: List = [
        (By.CSS_SELECTOR, "input[inputmode='tel']"),
        (By.CSS_SELECTOR, "input[data-testid='text-field-input'][type='tel']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
    ]
    wait = WebDriverWait(driver, max(15, int(timeout)))
    try:
        el = wait.until(lambda d: _find_first(d, selectors))
    except TimeoutException as e:
        raise YandexAuthError(
            "Не найдено поле телефона (inputmode=tel). " + _safe_page_hint(driver)
        ) from e
    try:
        el.click()
    except Exception:
        pass
    try:
        el.clear()
    except Exception:
        driver.execute_script("arguments[0].value = '';", el)
    time.sleep(0.15)
    el.send_keys(phone_digits)
    time.sleep(0.3)
    if not _click_dalee(driver, timeout=8.0):
        el.send_keys(Keys.ENTER)
    time.sleep(1.2)


def _click_dalee(driver: "WebDriver", timeout: float = 8.0) -> bool:
    candidates = [
        (By.CSS_SELECTOR, "[data-testid='add-user-next']"),
        (By.CSS_SELECTOR, "[data-testid='fln-next']"),
        (By.XPATH, "//button[.//span[normalize-space()='Далее'] or normalize-space()='Далее']"),
        (By.XPATH, "//button[contains(., 'Далее')]"),
    ]
    for by, val in candidates:
        if _wait_click(driver, by, val, min(timeout, 6.0)):
            return True
    return False


def _enter_password_and_submit(driver: "WebDriver", password: str, timeout: float) -> None:
    pwd_selectors: List = [
        (By.ID, "passp-field-passwd"),
        (By.CSS_SELECTOR, "input#passp-field-passwd"),
        (By.NAME, "passwd"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[autocomplete='current-password']"),
    ]
    wait = WebDriverWait(driver, max(20, int(timeout)))
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
                    "Требуется код подтверждения. " + _safe_page_hint(driver)
                ) from e
            raise YandexAuthError(
                "Не найдено поле пароля. " + _safe_page_hint(driver)
            ) from e
        except StaleElementReferenceException as e:
            if attempt >= 2:
                raise YandexAuthError(
                    "Страница сменилась при вводе пароля. Повторите проверку авторизации."
                ) from e
            time.sleep(0.5)


def page_indicates_auth_finished(driver: "WebDriver") -> bool:
    """Промежуточный успех Passport: код принят, идёт редирект/сессия."""
    u = (driver.current_url or "").lower()
    markers = (
        "auth/finished",
        "pwl-yandex/auth/finished",
        "oauth.yandex.ru/authorize",
        "/api/auth/web/login-yandex-id",
        "passport.yandex.ru/auth/session",
    )
    return any(m in u for m in markers)


def page_indicates_push_code(driver: "WebDriver") -> bool:
    """Экран ввода SMS/OTP-кода (сегменты или one-time-code)."""
    u = (driver.current_url or "").lower()
    # Успешный/переходный URL — не экран кода (иначе ложные «код не принят»).
    if page_indicates_auth_finished(driver):
        return False
    if "dzen.ru" in u and "passport" not in u:
        return False

    try:
        segments = driver.find_elements(By.CSS_SELECTOR, "[data-testid='code-field-segment']")
        visible_segments = [s for s in segments if s.is_displayed()]
        if len(visible_segments) >= 4:
            return True
        code_wrap = driver.find_elements(By.CSS_SELECTOR, "[data-testid='code-input']")
        if any(w.is_displayed() for w in code_wrap):
            return True
    except Exception:
        pass

    # Текст только как слабый сигнал: не сканируем весь page_source (много ложных срабатываний).
    try:
        title = (driver.title or "").lower()
    except Exception:
        title = ""
    title_markers = (
        "код из пуш",
        "код из смс",
        "введите код",
        "confirmation code",
        "one-time code",
    )
    if any(m in title for m in title_markers):
        return True

    url_markers = ("push-code", "/auth/push", "pwl-yandex/auth/push")
    if any(m in u for m in url_markers):
        try:
            for inp in driver.find_elements(By.CSS_SELECTOR, "input[autocomplete='one-time-code']"):
                if inp.is_displayed():
                    return True
        except Exception:
            pass

    try:
        visible_pwd = [
            p for p in driver.find_elements(By.CSS_SELECTOR, "input[type='password']") if p.is_displayed()
        ]
        if visible_pwd:
            return False
        for sel in (
            "input[autocomplete='one-time-code']",
            "input[inputmode='numeric'][data-testid='code-field-segment']",
        ):
            for inp in driver.find_elements(By.CSS_SELECTOR, sel):
                if inp.is_displayed():
                    return True
    except Exception:
        pass
    return False


def _visible_sms_reject_message(driver: "WebDriver") -> bool:
    """Видимое сообщение о неверном коде (не substring «ошиб» во всём HTML)."""
    phrases = (
        "неверн",
        "неправильн",
        "код истёк",
        "код истек",
        "incorrect code",
        "wrong code",
        "invalid code",
        "try again",
    )
    selectors = (
        "[role='alert']",
        "[data-testid='field-error']",
        ".passp-form-field__error",
        "[class*='error']",
        "[class*='Error']",
    )
    try:
        for sel in selectors:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if not el.is_displayed():
                        continue
                    text = (el.text or "").strip().lower()
                    if text and any(p in text for p in phrases):
                        return True
                except StaleElementReferenceException:
                    continue
    except Exception:
        pass
    return False


def page_indicates_name_form(driver: "WebDriver") -> bool:
    src = _lower_src(driver)
    return "введите имя и фамилию" in src


def page_indicates_account_suggest(driver: "WebDriver") -> bool:
    src = _lower_src(driver)
    if "выберите аккаунт" in src:
        return True
    try:
        return any(
            el.is_displayed()
            for el in driver.find_elements(By.CSS_SELECTOR, ".UserLogin-info, .AccountSuggestList-select-button")
        )
    except Exception:
        return False


def _check_authenticated(driver: "WebDriver") -> bool:
    u = (driver.current_url or "").lower()
    if page_indicates_auth_finished(driver):
        # Код принят / oauth в процессе — ещё не главная Дзена, но не «провал».
        return False
    if "passport.yandex.ru" in u and "session" not in u and "auth" in u:
        return False
    if page_indicates_push_code(driver):
        return False
    if _detect_captcha_block(driver):
        return False
    if page_indicates_name_form(driver) or page_indicates_account_suggest(driver):
        return False
    return "dzen.ru" in u


def _follow_auth_to_dzen(driver: "WebDriver") -> None:
    """С auth/finished / oauth — на dzen.ru, чтобы завершить cookie-сессию."""
    if not page_indicates_auth_finished(driver) and "passport.yandex" in (driver.current_url or "").lower():
        return
    if "dzen.ru" in (driver.current_url or "").lower() and "passport" not in (driver.current_url or "").lower():
        return
    try:
        driver.get("https://dzen.ru/")
        time.sleep(2.0)
        dismiss_passport_overlays(driver)
    except Exception:
        logger.debug("follow auth to dzen failed", exc_info=True)


def _try_fill_name_form(
    driver: "WebDriver",
    first_name: Optional[str],
    last_name: Optional[str],
) -> bool:
    if not page_indicates_name_form(driver):
        return False
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    if not first and not last:
        logger.warning("Экран ФИО есть, но имя/фамилия в профиле не заданы")
        return False
    try:
        inputs = [
            el
            for el in driver.find_elements(By.CSS_SELECTOR, "input[data-testid='text-field-input']")
            if el.is_displayed()
        ]
        if len(inputs) < 2:
            inputs = [
                el
                for el in driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if el.is_displayed()
            ]
        if len(inputs) < 2:
            return False
        if first:
            inputs[0].clear()
            inputs[0].send_keys(first)
        if last:
            inputs[1].clear()
            inputs[1].send_keys(last)
        time.sleep(0.3)
        if not _click_dalee(driver, timeout=5.0):
            _wait_click(driver, By.CSS_SELECTOR, "[data-testid='fln-next']", 5.0)
        time.sleep(1.0)
        return True
    except StaleElementReferenceException:
        return False
    except Exception:
        logger.debug("fill name form failed", exc_info=True)
        return False


def _try_select_account(driver: "WebDriver") -> bool:
    if not page_indicates_account_suggest(driver) and "выберите аккаунт" not in _lower_src(driver):
        # still try quick click if element visible
        pass
    candidates = [
        (By.CSS_SELECTOR, ".UserLogin-info"),
        (By.CSS_SELECTOR, ".AccountSuggestList-select-button"),
        (By.CSS_SELECTOR, "button.AccountSuggestList-select-button"),
    ]
    for by, val in candidates:
        if _wait_click(driver, by, val, _OPTIONAL_STEP_WAIT):
            time.sleep(1.0)
            return True
    return False


def complete_auth_after_code(
    driver: "WebDriver",
    password: str = "",
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    timeout: float = _POST_CODE_TIMEOUT_SEC,
    on_checkpoint: Optional[Callable[["WebDriver", str], None]] = None,
) -> None:
    """
    После SMS-кода: опционально ФИО → аккаунт → «Напомнить позже» → пароль.
    Цикл пока не dzen.ru или таймаут.
    """

    def _checkpoint(label: str) -> None:
        if not on_checkpoint:
            return
        try:
            on_checkpoint(driver, label)
        except Exception:
            logger.debug("dzen auth checkpoint %s failed", label, exc_info=True)

    deadline = time.time() + max(10.0, float(timeout))
    last_wait_shot = 0.0
    while time.time() < deadline:
        dismiss_passport_overlays(driver)
        if page_indicates_auth_finished(driver):
            _checkpoint("verify_yandex_auth_finished")
            _follow_auth_to_dzen(driver)
            _checkpoint("verify_yandex_after_finished_redirect")
        if _check_authenticated(driver):
            _checkpoint("verify_yandex_ok")
            return
        if page_indicates_push_code(driver):
            _checkpoint("verify_yandex_sms_still")
            return
        acted = False
        if page_indicates_name_form(driver):
            _checkpoint("verify_yandex_name_form")
            if _try_fill_name_form(driver, first_name, last_name):
                acted = True
                _checkpoint("verify_yandex_after_name")
        elif page_indicates_account_suggest(driver) or "выберите аккаунт" in _lower_src(driver):
            _checkpoint("verify_yandex_account_suggest")
            if _try_select_account(driver):
                acted = True
                _checkpoint("verify_yandex_after_account")
        elif dismiss_remind_later_popup(driver, timeout=_OPTIONAL_STEP_WAIT):
            acted = True
            time.sleep(0.5)
            _checkpoint("verify_yandex_after_remind_later")
        elif has_visible_password_field(driver):
            _checkpoint("verify_yandex_password")
            if (password or "").strip():
                try:
                    _enter_password_and_submit(
                        driver,
                        password,
                        float(getattr(settings, "YANDEX_PASSPORT_PASSWORD_TIMEOUT_SEC", 40)),
                    )
                    acted = True
                    _checkpoint("verify_yandex_after_password")
                except PushCodeRequiredError:
                    _checkpoint("verify_yandex_sms_after_password")
                    return
            else:
                logger.warning("Видно поле пароля, но пароль в профиле не задан")
        elif page_indicates_auth_finished(driver):
            acted = True
        if _check_authenticated(driver):
            _checkpoint("verify_yandex_ok")
            return
        if not acted:
            now = time.time()
            if now - last_wait_shot >= 2.0:
                _checkpoint("verify_yandex_waiting_next")
                last_wait_shot = now
            time.sleep(0.8)
        else:
            time.sleep(0.5)
    if not _check_authenticated(driver) and not page_indicates_push_code(driver):
        _checkpoint("verify_yandex_optional_timeout")
        logger.warning(
            "complete_auth_after_code: таймаут, url=%s",
            (driver.current_url or "")[:200],
        )


def dzen_entry_run_until_push_or_ok(
    driver: "WebDriver",
    login: str,
    password: str = "",
    on_checkpoint: Optional[Callable[["WebDriver", str], None]] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> DzenFlowResult:
    """
    Открывает dzen.ru, проходит сценарий входа по телефону.
    'push' — требуется SMS-код (драйвер остаётся открытым).
    'ok' — сессия готова (без экрана кода).
    """
    phone = (login or "").strip()
    if not phone:
        raise YandexAuthError("Пустой номер телефона (yandex_login)")
    # Валидация формата заранее
    _phone_or_raise(phone)

    def _checkpoint(label: str) -> None:
        if not on_checkpoint:
            return
        try:
            on_checkpoint(driver, label)
        except Exception:
            logger.debug("dzen auth checkpoint %s failed", label, exc_info=True)

    def _return_push(label: str) -> DzenFlowResult:
        _checkpoint(label)
        return "push"

    base = (getattr(settings, "DZEN_ENTRY_BASE_URL", None) or "https://dzen.ru/").strip()

    _checkpoint("verify_yandex_navigate")
    driver.get(base)
    time.sleep(2.0)
    dismiss_passport_overlays(driver)
    _checkpoint("verify_yandex_dzen_home")
    if _detect_captcha_block(driver):
        _checkpoint("verify_yandex_captcha")
        raise YandexAuthError(
            "Обнаружена проверка SmartCaptcha/«не робот» на dzen.ru. "
            "Headless-режим и дата-центр IP часто блокируются. Попробуйте вручную, другой сеть или SELENIUM_HEADLESS=false (отладка)."
        )

    _checkpoint("verify_yandex_before_voyti")
    _click_voyti_on_dzen(driver, 25.0)
    time.sleep(0.8)
    _wait_login_popup(driver, 15.0)
    dismiss_passport_overlays(driver)
    _checkpoint("verify_yandex_after_voyti")
    _click_yandex_id_entry(driver, 25.0)
    time.sleep(2.0)
    dismiss_passport_overlays(driver)
    _checkpoint("verify_yandex_id_entry")

    if _detect_captcha_block(driver):
        _checkpoint("verify_yandex_captcha_id")
        raise YandexAuthError("Капча/антибот на этапе Яндекс ID. " + _safe_page_hint(driver))

    if page_indicates_push_code(driver):
        return _return_push("verify_yandex_push_before_phone")

    _checkpoint("verify_yandex_before_phone_tab")
    _click_phone_tab(driver, 15.0)
    time.sleep(0.4)
    _checkpoint("verify_yandex_phone_tab")
    _enter_phone_and_submit(driver, phone, 25.0)
    dismiss_passport_overlays(driver)
    _checkpoint("verify_yandex_after_phone")

    if page_indicates_push_code(driver):
        return _return_push("verify_yandex_sms_code")

    # Иногда код появляется с задержкой
    _checkpoint("verify_yandex_wait_after_phone")
    try:
        WebDriverWait(driver, 12.0).until(
            lambda d: page_indicates_push_code(d)
            or _check_authenticated(d)
            or page_indicates_name_form(d)
            or page_indicates_account_suggest(d)
            or has_visible_password_field(d)
        )
    except TimeoutException:
        pass

    if page_indicates_push_code(driver):
        return _return_push("verify_yandex_sms_code_delayed")

    complete_auth_after_code(
        driver,
        password=password or "",
        first_name=first_name,
        last_name=last_name,
        on_checkpoint=on_checkpoint,
    )
    _checkpoint("verify_yandex_after_optional")

    if page_indicates_push_code(driver):
        return _return_push("verify_yandex_sms_after_optional")

    if _check_authenticated(driver):
        _checkpoint("verify_yandex_ok")
        return "ok"

    if "passport.yandex.ru" in (driver.current_url or "").lower():
        _checkpoint("verify_yandex_error")
        err = _find_first(
            driver,
            [(By.CSS_SELECTOR, ".passp-form-field__error"), (By.CSS_SELECTOR, "[role='alert']")],
        )
        msg = err.text.strip() if err else "Не удалось войти. Проверьте номер телефона."
        raise YandexAuthError(msg or "Ошибка входа в Яндекс ID.")

    if _check_authenticated(driver) or not page_indicates_push_code(driver):
        _checkpoint("verify_yandex_ok")
        return "ok"
    return _return_push("verify_yandex_sms_final")


def _find_code_segments(driver: "WebDriver") -> List:
    try:
        segs = [
            el
            for el in driver.find_elements(By.CSS_SELECTOR, "input[data-testid='code-field-segment']")
            if el.is_displayed()
        ]
        if segs:
            return segs
    except Exception:
        pass
    return []


def _find_push_code_input(driver: "WebDriver", timeout: float = 25.0):
    wait = WebDriverWait(driver, timeout)
    selectors: List = [
        (By.CSS_SELECTOR, "input[data-testid='code-field-segment']"),
        (By.CSS_SELECTOR, "input[autocomplete='one-time-code']"),
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
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
        (By.XPATH, "//button[contains(., 'Next') or contains(., 'Sign in') or contains(., 'Далее')]"),
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


def _wait_push_code_page_settled(driver: "WebDriver", timeout: float = 25.0) -> None:
    def settled(d: "WebDriver") -> bool:
        if page_indicates_auth_finished(d):
            return True
        if not page_indicates_push_code(d):
            return True
        if _visible_sms_reject_message(d):
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


def complete_auth_after_push_code(
    driver: "WebDriver",
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    on_checkpoint: Optional[Callable[["WebDriver", str], None]] = None,
) -> None:
    """После кода: опциональные экраны + пароль при необходимости."""
    complete_auth_after_code(
        driver,
        password=password or "",
        first_name=first_name,
        last_name=last_name,
        on_checkpoint=on_checkpoint,
    )


def dzen_entry_submit_push_code(
    driver: "WebDriver",
    code: str,
    on_checkpoint: Optional[Callable[["WebDriver", str], None]] = None,
) -> None:
    """Ввод 6-значного SMS-кода: по одной цифре в сегменты, иначе в одно поле."""
    c = re.sub(r"\D", "", (code or "").strip())
    if not c:
        raise YandexAuthError("Пустой код подтверждения")
    if len(c) != 6:
        raise YandexAuthError("Код должен содержать ровно 6 цифр")

    def _checkpoint(label: str) -> None:
        if not on_checkpoint:
            return
        try:
            on_checkpoint(driver, label)
        except Exception:
            logger.debug("dzen auth checkpoint %s failed", label, exc_info=True)

    dismiss_passport_overlays(driver)
    _checkpoint("verify_yandex_before_sms_input")

    last_stale: Optional[Exception] = None
    for attempt in range(4):
        try:
            segments = _find_code_segments(driver)
            if segments:
                for idx, digit in enumerate(c):
                    if idx >= len(segments):
                        break
                    seg = segments[idx]
                    try:
                        seg.click()
                    except StaleElementReferenceException:
                        segments = _find_code_segments(driver)
                        if idx >= len(segments):
                            break
                        seg = segments[idx]
                        seg.click()
                    try:
                        seg.clear()
                    except Exception:
                        driver.execute_script("arguments[0].value = '';", seg)
                    seg.send_keys(digit)
                    time.sleep(0.08)
                _checkpoint("verify_yandex_sms_digits_entered")
                time.sleep(0.4)
                _wait_push_code_page_settled(driver)
                dismiss_passport_overlays(driver)
                _checkpoint("verify_yandex_after_sms")
                break

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
            _checkpoint("verify_yandex_sms_digits_entered")
            _click_submit_after_push_code(driver)
            _wait_push_code_page_settled(driver)
            dismiss_passport_overlays(driver)
            _checkpoint("verify_yandex_after_sms")
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

    if page_indicates_auth_finished(driver):
        _checkpoint("verify_yandex_auth_finished")
        return

    if page_indicates_push_code(driver):
        if _visible_sms_reject_message(driver):
            _checkpoint("verify_yandex_sms_rejected")
            raise YandexAuthError("Код не принят. " + _safe_page_hint(driver))
        # Ещё на экране кода без явной ошибки — вызывающий может повторить.
        return

    # Код ушёл с экрана — успех или следующий шаг.
    _checkpoint("verify_yandex_after_sms_ok")


def login_yandex_dzen_entry(
    driver: "WebDriver",
    login: str,
    password: str = "",
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> None:
    """
    Полный сценарий dzen-входа без интерактивного кода (для publish/collect).
    Если нужен SMS — ошибка.
    """
    r = dzen_entry_run_until_push_or_ok(
        driver,
        login,
        password,
        first_name=first_name,
        last_name=last_name,
    )
    if r == "push":
        raise YandexAuthError(
            "Требуется код из SMS. Используйте проверку во вкладке «Авторизация» (двухшаговый вход) или войдите вручную."
        )


def yandex_auth_dispatch(
    driver: "WebDriver",
    login: str,
    password: str = "",
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> None:
    """Точка входа для ботов: dzen-флоу или прямой Passport по config."""
    if getattr(settings, "USE_DZEN_ENTRY_AUTH", True):
        login_yandex_dzen_entry(
            driver,
            login,
            password,
            first_name=first_name,
            last_name=last_name,
        )
    else:
        from .yandex_auth import login_yandex_passport

        login_yandex_passport(driver, login, password)
