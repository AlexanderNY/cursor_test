"""Фабрика WebDriver для Chromium — fallback вход через веб-форму (см. selenium_instagram_login).

При неудаче instagrapi и включённом INSTAGRAM_SELENIUM_FALLBACK_ENABLED выполняется
автоматический ввод логина/пароля; challenge/2FA по-прежнему требуют ручного шага.
Основной путь: instagrapi + сессия в БД (см. instagram_client).
"""

import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)


def create_chrome_driver() -> webdriver.Chrome:
    """Создаёт Chrome/Chromium с опциями для headless и Docker (как dzen-bot)."""
    options = Options()
    if getattr(settings, "SELENIUM_HEADLESS", True):
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    chrome_bin = os.environ.get("CHROME_BIN") or getattr(settings, "CHROME_BIN", "") or ""
    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH") or getattr(settings, "CHROMEDRIVER_PATH", "") or ""
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(getattr(settings, "SELENIUM_PAGE_LOAD_TIMEOUT", 60))
    driver.implicitly_wait(getattr(settings, "SELENIUM_IMPLICIT_WAIT", 5))
    return driver


def open_instagram_login_page() -> webdriver.Chrome:
    """Открывает страницу логина Instagram (для ручной отладки / обхода challenge)."""
    driver = create_chrome_driver()
    driver.get("https://www.instagram.com/accounts/login/")
    logger.info("Instagram login page opened (manual interaction may be required)")
    return driver
