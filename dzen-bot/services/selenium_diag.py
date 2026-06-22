"""Диагностика: скриншот при ошибке Selenium → S3 (ключ содержит подстроку «diag»)."""

from __future__ import annotations

import asyncio
import base64
import logging
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional

from config import settings
from storage_helper import get_storage

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


def _sanitize_label(label: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", (label or "").strip())[:100]
    return s or "step"


async def _put_png(key: str, png: bytes) -> None:
    storage = get_storage()
    if not storage:
        return
    await storage.put(key, png, content_type="image/png")


async def _put_png_and_presigned_url(
    key: str, png: bytes, expires_in: int = 3600
) -> tuple[Optional[str], Optional[str]]:
    storage = get_storage()
    if not storage:
        return None, None
    await storage.put(key, png, content_type="image/png")
    url = await storage.get_presigned_url(key, expires_in=expires_in)
    return key, url


def _build_diag_s3_key(label: str, user_id: Optional[int]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid_part = f"uid{user_id}" if user_id is not None else "nouid"
    safe = _sanitize_label(label)
    prefix = (settings.S3_DIAG_PREFIX or "dzen/diag").strip().strip("/")
    return f"{prefix}/diag_selenium_{ts}_{uid_part}_{safe}.png"


def _png_to_jpeg_data_url(png: bytes, *, max_width: int = 800, quality: int = 75) -> Optional[str]:
    """Сжатый JPEG для inline-отображения в UI (не зависит от presigned MinIO)."""
    try:
        from PIL import Image

        img = Image.open(BytesIO(png))
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        width, height = img.size
        if width > max_width:
            height = max(1, int(height * max_width / width))
            img = img.resize((max_width, height), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        logger.warning("selenium_diag: JPEG encode failed (%s), fallback to PNG data URL", e)
        return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def _upload_png_to_s3(key: str, png: bytes) -> Optional[str]:
    if not get_storage():
        return None
    try:
        asyncio.run(_put_png(key, png))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e).lower() or "already running" in str(
            str(e)
        ).lower():
            logger.warning("selenium_diag: cannot run async S3 upload in this context (%s)", e)
            return None
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        return None
    except Exception as e:
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        return None
    bucket = getattr(settings, "S3_BUCKET", "")
    logger.info("selenium_diag: screenshot uploaded s3://%s/%s", bucket, key)
    return key


def capture_diag_for_ui(
    driver: Optional["WebDriver"],
    label: str,
    *,
    user_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Диагностика для verify-yandex: архив PNG в S3 + inline JPEG data URL для UI.
    Returns:
        {"diag_image_url": str|None, "diag_s3_key": str|None}
    """
    if driver is None:
        return {"diag_image_url": None, "diag_s3_key": None}
    try:
        png = driver.get_screenshot_as_png()
    except Exception as e:
        logger.warning("selenium_diag: get_screenshot_as_png failed: %s", e)
        return {"diag_image_url": None, "diag_s3_key": None}

    jpeg_url = _png_to_jpeg_data_url(png)
    s3_key = _upload_png_to_s3(_build_diag_s3_key(label, user_id), png)
    return {"diag_image_url": jpeg_url, "diag_s3_key": s3_key}


def upload_selenium_diag_screenshot(
    driver: "WebDriver",
    label: str,
    *,
    user_id: Optional[int] = None,
) -> Optional[str]:
    """
    Делает PNG-скриншот и загружает в S3. Имя объекта обязательно содержит «diag».

    Returns:
        Ключ объекта в бакете или None (S3 не настроен, сбой снимка/загрузки).
    """
    if driver is None:
        return None
    try:
        png = driver.get_screenshot_as_png()
    except Exception as e:
        logger.warning("selenium_diag: get_screenshot_as_png failed: %s", e)
        return None

    if not get_storage():
        logger.debug("selenium_diag: S3 not configured, skip upload")
        return None

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid_part = f"uid{user_id}" if user_id is not None else "nouid"
    safe = _sanitize_label(label)
    prefix = (settings.S3_DIAG_PREFIX or "dzen/diag").strip().strip("/")
    # Требование: имя файла содержит «diag»
    key = f"{prefix}/diag_selenium_{ts}_{uid_part}_{safe}.png"

    try:
        asyncio.run(_put_png(key, png))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e).lower() or "already running" in str(
            str(e)
        ).lower():
            logger.warning(
                "selenium_diag: cannot run async S3 upload in this context (%s); skip upload", e
            )
            return None
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        return None
    except Exception as e:
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        return None

    bucket = getattr(settings, "S3_BUCKET", "")
    logger.info("selenium_diag: screenshot uploaded s3://%s/%s", bucket, key)
    return key


def upload_selenium_diag_screenshot_with_url(
    driver: "WebDriver",
    label: str,
    *,
    user_id: Optional[int] = None,
    expires_in: int = 3600,
) -> tuple[Optional[str], Optional[str]]:
    """
    Скриншот в S3 и presigned URL для отображения в UI.
    Returns:
        (s3_key, presigned_url) или (None, None).
    """
    if driver is None:
        return None, None
    try:
        png = driver.get_screenshot_as_png()
    except Exception as e:
        logger.warning("selenium_diag: get_screenshot_as_png failed: %s", e)
        return None, None

    if not get_storage():
        # Fallback for UI diagnostics when S3/presigned is not configured.
        # This keeps the screenshot visible in auth tab via <img src="data:...">.
        data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        return None, data_url

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid_part = f"uid{user_id}" if user_id is not None else "nouid"
    safe = _sanitize_label(label)
    prefix = (settings.S3_DIAG_PREFIX or "dzen/diag").strip().strip("/")
    key = f"{prefix}/diag_selenium_{ts}_{uid_part}_{safe}.png"

    try:
        k, url = asyncio.run(_put_png_and_presigned_url(key, png, expires_in=expires_in))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e).lower() or "already running" in str(
            str(e)
        ).lower():
            logger.warning("selenium_diag: cannot run async S3 in this context (%s)", e)
            data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
            return None, data_url
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        return None, data_url
    except Exception as e:
        logger.warning("selenium_diag: S3 upload failed: %s", e)
        data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        return None, data_url

    if k:
        logger.info("selenium_diag: screenshot s3://%s/%s presigned ok", getattr(settings, "S3_BUCKET", ""), k)
    return k, url


def capture_selenium_error_to_s3(
    driver: Optional["WebDriver"],
    label: str,
    *,
    user_id: Optional[int] = None,
) -> Optional[str]:
    """
    Вызывать из except-блоков при ошибке сценария Selenium (драйвер ещё открыт).
    Возвращает ключ S3 или None.
    """
    if driver is None:
        return None
    return upload_selenium_diag_screenshot(driver, label, user_id=user_id)


def capture_selenium_error_to_s3_with_url(
    driver: Optional["WebDriver"],
    label: str,
    *,
    user_id: Optional[int] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Как capture_selenium_error_to_s3, плюс presigned URL."""
    if driver is None:
        return None, None
    return upload_selenium_diag_screenshot_with_url(driver, label, user_id=user_id)
