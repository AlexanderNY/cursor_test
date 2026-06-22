"""Загрузка диагностических скриншотов Selenium в S3 (синхронно, без asyncio)."""

from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)


def upload_selenium_diag_screenshot_png(png_bytes: bytes, reason_slug: str) -> Optional[str]:
    """
    Кладёт PNG в бакет. Имя ключа всегда содержит подстроку \"diag\".

    Возвращает ключ объекта или None при отсутствии конфига/ошибке.
    """
    if not png_bytes:
        return None
    if not getattr(settings, "S3_ACCESS_KEY", None) or not getattr(settings, "S3_SECRET_KEY", None):
        logger.debug("S3 credentials not set, skip diag screenshot upload")
        return None
    bucket = (getattr(settings, "S3_BUCKET", None) or "").strip()
    if not bucket:
        logger.debug("S3_BUCKET not set, skip diag screenshot upload")
        return None

    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (reason_slug or "unknown")[:80])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    uid = uuid.uuid4().hex[:8]
    key = f"instagram/selenium-diag/{ts}_instagram_selenium_diag_{safe}_{uid}.png"

    try:
        import boto3
        from botocore.client import Config
    except ImportError:
        logger.warning("boto3 not available, cannot upload diag screenshot")
        return None

    endpoint = (getattr(settings, "S3_ENDPOINT_URL", None) or "").strip() or None
    use_ssl = bool(getattr(settings, "S3_USE_SSL", True))

    try:
        session = boto3.session.Session()
        client = session.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
            use_ssl=use_ssl,
            config=Config(signature_version="s3v4"),
        )
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=png_bytes,
            ContentType="image/png",
        )
        logger.info("Stored selenium diag screenshot s3://%s/%s", bucket, key)
        return key
    except Exception as e:
        logger.warning("Failed to upload selenium diag screenshot: %s", e, exc_info=True)
        return None


def try_capture_and_upload_diag(driver: Any, reason_slug: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Скриншот: загрузка в S3 + base64 для UI (без префикса data:).

    Возвращает (s3_key, base64_str). При слишком большом PNG base64 опускается, S3 остаётся.
    """
    if driver is None:
        return None, None
    try:
        png = driver.get_screenshot_as_png()
    except Exception as e:
        logger.warning("Selenium diag screenshot capture skipped: %s", e)
        return None, None

    max_kb = int(getattr(settings, "SELENIUM_DIAG_MAX_BASE64_KB", 512) or 512)
    max_bytes = max(64, max_kb) * 1024
    b64: Optional[str] = None
    if len(png) <= max_bytes:
        b64 = base64.b64encode(png).decode("ascii")
    else:
        logger.warning(
            "Diagnostic PNG %s bytes exceeds SELENIUM_DIAG_MAX_BASE64_KB=%s, omitting base64 in API",
            len(png),
            max_kb,
        )

    s3_key = upload_selenium_diag_screenshot_png(png, reason_slug)
    return s3_key, b64
