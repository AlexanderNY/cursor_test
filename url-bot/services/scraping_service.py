"""Сервис скрапинга: переход по URL, извлечение по XPath, скриншот элемента."""

import base64
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import settings

logger = logging.getLogger(__name__)


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


def _create_driver() -> webdriver.Chrome:
    """Создаёт headless Chrome/Chromium driver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.isfile(chromedriver_path):
        service = Service(chromedriver_path)
    else:
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


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
    driver = None
    try:
        driver = _create_driver()
        driver.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT_SECONDS)
        driver.get(url)
        wait = WebDriverWait(driver, settings.ELEMENT_WAIT_TIMEOUT_SECONDS)
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
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
        logger.exception("Scraping failed: %s", e)
        result["error"] = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning("Driver quit: %s", e)
    return result


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


scraping_service = ScrapingService()
