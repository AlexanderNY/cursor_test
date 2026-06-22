"""
Хелперы для Selenium на instagram.com: поиск по name, русским подписям, клики.
Вёрстка/локали меняются — несколько стратегий с fallback; не гарантирует устойчивость 24/7.
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Фрагменты подписей (RU) и (EN) для устойчивости
_USERNAME_LABEL_RU = "Имя пользователя, номер мобильного телефона или электронный адрес"
_PASSWORD_RU = "Пароль"

_USERNAME_FRAGMENTS_EN = [
    "username",
    "email",
    "phone number",
    "Phone number",
    "мобильного",
]


def _find_first(
    driver: WebDriver, selectors: List[Tuple[str, str]]
) -> Optional[WebElement]:
    for by, value in selectors:
        try:
            for el in driver.find_elements(by, value):
                if el.is_displayed():
                    return el
        except WebDriverException:
            continue
    return None


def click_if_visible(driver: WebDriver, by: str, value: str, timeout: float = 8) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        el.click()
        time.sleep(0.3)
        return True
    except (TimeoutException, WebDriverException):
        return False


def find_email_input_and_fill(
    driver: WebDriver, username: str, wait: WebDriverWait
) -> bool:
    """1) input[name=email], иначе клик по подписи и ввод. Возвращает True при успехе."""
    selectors: List[Tuple[str, str]] = [
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.NAME, "email"),
        (By.XPATH, "//input[@name='email']"),
    ]
    for by, value in selectors:
        try:
            el = wait.until(EC.presence_of_element_located((by, value)))
            if el and el.is_displayed():
                el.clear()
                el.send_keys(username)
                return True
        except (TimeoutException, WebDriverException):
            continue

    # Клик по зоне с длинной русской подписью, затем снова name=email
    for xpath in (
        f"//span[contains(., '{_USERNAME_LABEL_RU[:20]}')]",
        f"//*[contains(., '{_USERNAME_LABEL_RU}') and not(self::script)]",
    ):
        try:
            for node in driver.find_elements(By.XPATH, xpath)[:3]:
                if not node.is_displayed():
                    continue
                try:
                    node.click()
                except WebDriverException:
                    driver.execute_script("arguments[0].click();", node)
                time.sleep(0.4)
                el = _find_first(
                    driver, [(By.CSS_SELECTOR, "input[name='email']"), (By.NAME, "email")]
                )
                if el:
                    el.clear()
                    el.send_keys(username)
                    return True
        except WebDriverException:
            continue

    # aria-label на инпуте
    for frag in _USERNAME_FRAGMENTS_EN:
        try:
            for el in driver.find_elements(
                By.XPATH,
                f"//input[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{frag.lower()}') or contains(@aria-label, '{frag}')]",
            ):
                if el.is_displayed():
                    el.clear()
                    el.send_keys(username)
                    return True
        except WebDriverException:
            continue

    # following input after label
    for xpath in (
        "//label[contains(., 'Имя пользователя')]/following::input[1]",
        "//div[contains(., 'мобильного') or contains(., 'телефона')]/descendant::input[1]",
    ):
        try:
            el = driver.find_element(By.XPATH, xpath)
            if el.is_displayed() and el.tag_name.lower() == "input":
                el.clear()
                el.send_keys(username)
                return True
        except WebDriverException:
            continue

    return False


def find_password_input_and_fill(
    driver: WebDriver, password: str, wait: WebDriverWait
) -> bool:
    for by, value in [
        (By.CSS_SELECTOR, "input[name='pass']"),
        (By.NAME, "pass"),
    ]:
        try:
            el = wait.until(EC.presence_of_element_located((by, value)))
            if el and el.is_displayed():
                el.clear()
                el.send_keys(password)
                return True
        except (TimeoutException, WebDriverException):
            continue

    # Текст «Пароль» — клик и ввод
    try:
        for node in driver.find_elements(
            By.XPATH, f"//span[contains(., '{_PASSWORD_RU}') or contains(.,'Пароль')]"
        )[:5]:
            if not node.is_displayed():
                continue
            try:
                node.click()
            except WebDriverException:
                pass
            time.sleep(0.3)
            el = _find_first(
                driver,
                [
                    (By.CSS_SELECTOR, "input[name='pass']"),
                    (By.NAME, "pass"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                ],
            )
            if el:
                el.clear()
                el.send_keys(password)
                return True
    except WebDriverException:
        pass

    for el in driver.find_elements(By.CSS_SELECTOR, "input[type='password']"):
        if el.is_displayed():
            el.clear()
            el.send_keys(password)
            return True
    return False


def find_and_click_login_button(driver: WebDriver, _wait: WebDriverWait) -> bool:
    candidates: List[Tuple[str, str]] = [
        (By.XPATH, "//div[@aria-label='Вход']"),
        (By.XPATH, "//*[@aria-label='Вход']"),
        (
            By.XPATH,
            "//div[contains(translate(.,'ВОЙТИ','войти'),'войти') and (contains(.,'Войти') or @role='button')]",
        ),
        (By.XPATH, "//button[contains(.,'Войти') or contains(.,'войти')]"),
        (By.XPATH, "//*[@role='button' and (contains(.,'Войти') or contains(.,'Log in') or contains(.,'Log In'))]"),
    ]
    for by, value in candidates:
        try:
            el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, value)))
            if el:
                el.click()
                return True
        except (TimeoutException, WebDriverException):
            continue

    for by, value in [
        (By.XPATH, "//form//button[@type='submit']"),
    ]:
        if click_if_visible(driver, by, value, 5):
            return True
    return False
