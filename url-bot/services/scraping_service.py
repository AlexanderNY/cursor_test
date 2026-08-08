"""Сервис скрапинга: переход по URL, извлечение по XPath, скриншот элемента."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import signal
import threading
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Optional

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import settings
from services.url_safety import UnsafeUrlError, validate_public_http_url

logger = logging.getLogger(__name__)

_selenium_semaphore: Optional[asyncio.Semaphore] = None
_semaphore_lock = threading.Lock()


def get_selenium_semaphore() -> asyncio.Semaphore:
    """Lazy singleton Semaphore для лимита параллельных Chrome."""
    global _selenium_semaphore
    if _selenium_semaphore is None:
        with _semaphore_lock:
            if _selenium_semaphore is None:
                n = max(1, int(settings.SELENIUM_MAX_CONCURRENT))
                _selenium_semaphore = asyncio.Semaphore(n)
    return _selenium_semaphore


def _compress_screenshot(png_bytes: bytes) -> bytes:
    """Сжимает PNG в JPEG: ресайз по длинной стороне, качество 80–85%."""
    if not png_bytes:
        return b""
    max_side = getattr(settings, "SCREENSHOT_MAX_PIXELS", 1920) or 1920
    quality = getattr(settings, "SCREENSHOT_JPEG_QUALITY", 85) or 85
    try:
        img = Image.open(BytesIO(png_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        w, h = img.size
        if w > max_side or h > max_side:
            if w >= h:
                new_w, new_h = max_side, int(h * max_side / w)
            else:
                new_w, new_h = int(w * max_side / h), max_side
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception as e:
        logger.warning("Screenshot compress failed, using original: %s", e)
        return png_bytes


def _save_screenshot_to_disk(jpeg_bytes: bytes, user_id: int) -> str | None:
    """Сохраняет JPEG в UPLOAD_DIR/uploads/url/{user_id}/{date}/{uuid}.jpg. Возвращает относительный путь."""
    upload_dir = getattr(settings, "UPLOAD_DIR", "") or ""
    if not upload_dir or not jpeg_bytes:
        return None
    try:
        date_part = datetime.utcnow().strftime("%Y-%m-%d")
        dir_path = os.path.join(upload_dir, "uploads", "url", str(user_id), date_part)
        os.makedirs(dir_path, exist_ok=True)
        name = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(dir_path, name)
        with open(file_path, "wb") as f:
            f.write(jpeg_bytes)
        return f"/uploads/url/{user_id}/{date_part}/{name}"
    except Exception as e:
        logger.warning("Screenshot save to disk failed: %s", e)
        return None


def _kill_process_tree(pid: int) -> None:
    """Принудительно завершает процесс (и пытается дочерние на Unix)."""
    if pid <= 0:
        return
    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
        else:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except Exception as e:
        logger.warning("Failed to kill process pid=%s: %s", pid, e)


def _quit_driver(driver: webdriver.Chrome | None) -> None:
    """Корректный quit; при зависании/ошибке — kill chromedriver PID."""
    if driver is None:
        return
    service_proc = None
    try:
        service = getattr(driver, "service", None)
        service_proc = getattr(service, "process", None) if service else None
    except Exception:
        service_proc = None

    quit_done = threading.Event()

    def _do_quit() -> None:
        try:
            driver.quit()
        except Exception as e:
            logger.warning("Driver quit error: %s", e)
        finally:
            quit_done.set()

    t = threading.Thread(target=_do_quit, name="selenium-quit", daemon=True)
    t.start()
    if not quit_done.wait(timeout=5.0):
        logger.warning("Driver quit hung; killing chromedriver process")
        pid = getattr(service_proc, "pid", None) if service_proc else None
        if pid:
            _kill_process_tree(int(pid))
        try:
            if service_proc and service_proc.poll() is None:
                service_proc.kill()
        except Exception as e:
            logger.warning("service.process.kill failed: %s", e)


def _create_driver() -> webdriver.Chrome:
    """Создаёт headless Chrome/Chromium driver с eager page load."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.page_load_strategy = "eager"
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT_SECONDS)
    driver.set_script_timeout(settings.PAGE_LOAD_TIMEOUT_SECONDS)
    driver.implicitly_wait(0)
    return driver


def scrape_url(
    url: str,
    xpath: str,
    take_screenshot: bool,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Открывает URL, находит элемент по XPath, извлекает текст и опционально скриншот элемента.
    Скриншот сжимается (resize + JPEG). При заданном UPLOAD_DIR и user_id сохраняется на диск.

    Args:
        url: URL страницы
        xpath: XPath селектор элемента
        take_screenshot: делать скриншот элемента
        user_id: опционально, для сохранения файла в uploads/url/{user_id}/...

    Returns:
        {"text", "screenshot_base64" | "screenshot_path", "error"}
    """
    result: dict[str, Any] = {
        "text": None,
        "screenshot_base64": None,
        "screenshot_path": None,
        "error": None,
    }
    try:
        safe_url = validate_public_http_url(url)
    except UnsafeUrlError as e:
        logger.warning("SSRF blocked URL=%r: %s", url, e)
        result["error"] = f"URL not allowed: {e}"
        return result

    driver: webdriver.Chrome | None = None
    hard_fired = threading.Event()
    timer: threading.Timer | None = None

    def _force_stop() -> None:
        hard_fired.set()
        logger.warning("Scrape hard timeout (%ss) for url=%r", settings.SCRAPE_HARD_TIMEOUT_SECONDS, url)
        _quit_driver(driver)

    try:
        driver = _create_driver()
        hard_seconds = max(1, int(settings.SCRAPE_HARD_TIMEOUT_SECONDS))
        timer = threading.Timer(hard_seconds, _force_stop)
        timer.daemon = True
        timer.start()

        driver.get(safe_url)
        if hard_fired.is_set():
            result["error"] = "Scrape hard timeout"
            return result

        wait = WebDriverWait(driver, settings.ELEMENT_WAIT_TIMEOUT_SECONDS)
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        if hard_fired.is_set():
            result["error"] = "Scrape hard timeout"
            return result

        result["text"] = element.text or ""
        if take_screenshot:
            png_bytes = element.screenshot_as_png
            jpeg_bytes = _compress_screenshot(png_bytes)
            upload_dir = getattr(settings, "UPLOAD_DIR", "") or ""
            if upload_dir and user_id is not None:
                path = _save_screenshot_to_disk(jpeg_bytes, user_id)
                if path:
                    result["screenshot_path"] = path
                else:
                    result["screenshot_base64"] = base64.b64encode(jpeg_bytes).decode("ascii")
            else:
                result["screenshot_base64"] = base64.b64encode(jpeg_bytes).decode("ascii")
    except Exception as e:
        if hard_fired.is_set():
            result["error"] = "Scrape hard timeout"
        else:
            logger.exception("Scraping failed: %s", e)
            result["error"] = str(e)
    finally:
        if timer is not None:
            timer.cancel()
        _quit_driver(driver)
    return result


async def scrape_url_async(
    url: str,
    xpath: str,
    take_screenshot: bool = False,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Async-обёртка: ждёт слот Semaphore, затем scrape_url в thread.
    Семафор держится до завершения треда (не отпускать по cancel to_thread).
    """
    sem = get_selenium_semaphore()
    acquire_timeout = float(settings.SELENIUM_ACQUIRE_TIMEOUT_SECONDS)
    try:
        await asyncio.wait_for(sem.acquire(), timeout=acquire_timeout)
    except asyncio.TimeoutError:
        logger.warning(
            "Selenium busy: no slot within %.1fs (max_concurrent=%s)",
            acquire_timeout,
            settings.SELENIUM_MAX_CONCURRENT,
        )
        return {
            "text": None,
            "screenshot_base64": None,
            "screenshot_path": None,
            "error": "Selenium busy",
        }

    try:
        return await asyncio.to_thread(scrape_url, url, xpath, take_screenshot, user_id)
    finally:
        sem.release()


class ScrapingService:
    """Сервис скрапинга (фасад для совместимости)."""

    def scrape(
        self,
        url: str,
        xpath: str,
        take_screenshot: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        return scrape_url(url, xpath, take_screenshot, user_id)

    async def scrape_async(
        self,
        url: str,
        xpath: str,
        take_screenshot: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        return await scrape_url_async(url, xpath, take_screenshot, user_id)


scraping_service = ScrapingService()
