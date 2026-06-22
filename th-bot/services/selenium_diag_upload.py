"""Загрузка диагностических PNG скриншотов Selenium в S3."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def upload_selenium_diagnostic_png(
    user_id: int,
    session_id: int,
    png: bytes,
) -> Optional[str]:
    """
    Сохраняет PNG в S3. Ключ обязан содержать подстроку «diag».
    При отключённом S3 возвращает None.
    """
    if not png:
        return None
    try:
        from storage_helper import get_storage
    except Exception:
        return None
    storage = get_storage()
    if not storage:
        logger.info("th-bot Selenium diag: S3 not configured, screenshot not uploaded")
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"th-bot/selenium/diag_meta_user{user_id}_session{session_id}_{ts}.png"
    assert "diag" in key
    try:
        await storage.put(key, png, content_type="image/png")
        logger.info("th-bot Selenium diag screenshot stored s3://%s/%s", getattr(storage, "bucket", "?"), key)
        return key
    except Exception:
        logger.warning("th-bot Selenium diag: S3 upload failed", exc_info=True)
        return None
