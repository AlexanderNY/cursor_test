"""Фабрика WebDriver для Chromium (tw-bot, проверка X через Selenium)."""
import logging
import os
from typing import Any, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)


def create_chrome_driver(proxy: Optional[Dict[str, Any]] = None) -> webdriver.Chrome:
    """Создаёт Chrome/Chromium; опционально HTTP-прокси без авторизации (host:port)."""
    options = Options()
    if settings.SELENIUM_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    if proxy and proxy.get("host"):
        host = str(proxy["host"]).strip()
        port = proxy.get("port")
        if host:
            port_s = str(int(port)) if port is not None else "80"
            options.add_argument(f"--proxy-server=http://{host}:{port_s}")

    chrome_bin = os.environ.get("CHROME_BIN") or getattr(settings, "CHROME_BIN", "") or ""
    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH") or getattr(settings, "CHROMEDRIVER_PATH", "") or ""
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(settings.SELENIUM_PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(settings.SELENIUM_IMPLICIT_WAIT)
    return driver
