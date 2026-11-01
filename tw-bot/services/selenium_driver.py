"""Фабрика WebDriver для Chromium (tw-bot, проверка X через Selenium)."""
import asyncio
import logging
import os
import re
import subprocess
import threading
from typing import Any, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)

_UA_CACHE: Optional[tuple[str, str]] = None
_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = window.chrome || { runtime: {} };
"""

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


def user_agent_metadata(version: str) -> Dict[str, Any]:
    """Client Hints как у обычного Chrome. Пустой brands X считает ботом на шаге входа."""
    major = (version or "131.0.0.0").split(".", 1)[0] or "131"
    full = version or "131.0.0.0"
    brands = [
        {"brand": "Chromium", "version": major},
        {"brand": "Google Chrome", "version": major},
        {"brand": "Not.A/Brand", "version": "99"},
    ]
    return {
        "brands": brands,
        "fullVersionList": [
            {"brand": item["brand"], "version": full if item["brand"] != "Not.A/Brand" else "99.0.0.0"}
            for item in brands
        ],
        "platform": "Linux",
        "platformVersion": "6.8.0",
        "architecture": "x86",
        "model": "",
        "mobile": False,
        "bitness": "64",
        "wow64": False,
    }


def _chrome_identity(chrome_bin: str) -> tuple[str, str]:
    """UA без HeadlessChrome и версия Chromium для Client Hints."""
    global _UA_CACHE
    if _UA_CACHE:
        return _UA_CACHE
    version = "131.0.0.0"
    binary = (chrome_bin or "").strip() or "chromium"
    try:
        completed = subprocess.run(
            [binary, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", completed.stdout or "")
        if match:
            version = match.group(1)
    except (OSError, subprocess.TimeoutExpired):
        logger.debug("chromium --version failed", exc_info=True)
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{version} Safari/537.36"
    )
    _UA_CACHE = (user_agent, version)
    return _UA_CACHE


def _chrome_user_agent(chrome_bin: str) -> str:
    """Обычный Chrome UA. Токен HeadlessChrome x.com встречает ответом HTTP 403."""
    return _chrome_identity(chrome_bin)[0]


def _apply_browser_stealth(driver: webdriver.Chrome, user_agent: str, version: str) -> None:
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": _STEALTH_SCRIPT},
        )
    except Exception:
        logger.debug("X stealth init script failed", exc_info=True)
    try:
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": user_agent,
                "acceptLanguage": "en-US,en;q=0.9",
                "platform": "Linux x86_64",
                "userAgentMetadata": user_agent_metadata(version),
            },
        )
    except Exception:
        logger.debug("X stealth UA override failed", exc_info=True)


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
    options.add_experimental_option("useAutomationExtension", False)
    chrome_bin = os.environ.get("CHROME_BIN") or getattr(settings, "CHROME_BIN", "") or ""
    user_agent, chrome_version = _chrome_identity(chrome_bin)
    options.add_argument(f"--user-agent={user_agent}")

    if proxy and proxy.get("host"):
        host = str(proxy["host"]).strip()
        port = proxy.get("port")
        if host:
            port_s = str(int(port)) if port is not None else "80"
            options.add_argument(f"--proxy-server=http://{host}:{port_s}")

    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH") or getattr(settings, "CHROMEDRIVER_PATH", "") or ""
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(settings.SELENIUM_PAGE_LOAD_TIMEOUT)
    # Явные ожидания в логине. Ненулевой implicit превращает каждый пустой find в паузу.
    driver.implicitly_wait(0)
    _apply_browser_stealth(driver, user_agent, chrome_version)
    return driver
