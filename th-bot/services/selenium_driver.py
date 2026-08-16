"""Фабрика WebDriver для Chromium (по образцу dzen-bot)."""

import asyncio
import logging
import os
import threading
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)

_selenium_semaphore: Optional[asyncio.Semaphore] = None
_semaphore_lock = threading.Lock()


def get_selenium_semaphore() -> asyncio.Semaphore:
    """Limit parallel Chrome (SELENIUM_MAX_CONCURRENT)."""
    global _selenium_semaphore
    if _selenium_semaphore is None:
        with _semaphore_lock:
            if _selenium_semaphore is None:
                n = max(1, int(getattr(settings, "SELENIUM_MAX_CONCURRENT", 2) or 2))
                _selenium_semaphore = asyncio.Semaphore(n)
    return _selenium_semaphore


def create_chrome_driver() -> webdriver.Chrome:
    """Создаёт Chrome/Chromium с опциями для headless и Docker."""
    options = Options()
    if settings.SELENIUM_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en")
    chrome_bin = os.environ.get("CHROME_BIN") or ""
    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH") or ""
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(float(settings.SELENIUM_PAGE_LOAD_TIMEOUT))
    driver.implicitly_wait(float(settings.SELENIUM_IMPLICIT_WAIT))
    return driver
