"""Загрузка и чтение медиафайлов опросов в S3."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from config import settings
from shared_storage import get_storage

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

PUBLIC_FILENAME_RE = re.compile(
    r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.[a-z0-9]+$",
    re.IGNORECASE,
)


def get_media_storage():
    return get_storage(
        bucket=settings.S3_BUCKET,
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        access_key=settings.S3_ACCESS_KEY or None,
        secret_key=settings.S3_SECRET_KEY or None,
        use_ssl=settings.S3_USE_SSL,
    )


def build_s3_key(filename: str) -> str:
    prefix = (settings.GAME_MEDIA_S3_PREFIX or "uploads/game").strip().strip("/")
    return f"{prefix}/{filename}"


def build_public_url(filename: str) -> str:
    base = (settings.GAME_MEDIA_PUBLIC_BASE_URL or "").rstrip("/")
    return f"{base}/tg/game/media/{filename}"


def resolve_public_media_url(image_url: str | None) -> str | None:
    """Подставляет актуальный публичный base URL (для старых записей с localhost)."""
    if not image_url:
        return None
    match = re.search(r"/tg/game/media/([^/?#]+)$", image_url.strip())
    if not match:
        return image_url
    return build_public_url(match.group(1))


def extract_media_filename(image_url: str | None) -> str | None:
    if not image_url:
        return None
    match = re.search(r"/tg/game/media/([^/?#]+)$", image_url.strip())
    if not match:
        return None
    filename = match.group(1)
    return filename if validate_public_filename(filename) else None


def guess_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return MIME_BY_EXT.get(ext, "application/octet-stream")


def validate_upload_filename(original_filename: str | None) -> tuple[str, str]:
    if not original_filename:
        raise ValueError("Filename is required")
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Allowed formats: JPG, PNG, WebP, GIF")
    stored_name = f"{uuid.uuid4()}{ext}"
    return stored_name, guess_content_type(stored_name)


def validate_public_filename(filename: str) -> bool:
    return bool(PUBLIC_FILENAME_RE.match(filename))


async def upload_media_file(
    *,
    body: bytes,
    original_filename: str | None,
) -> tuple[str, str, str, str]:
    if not body:
        raise ValueError("Empty file")
    if len(body) > 10 * 1024 * 1024:
        raise ValueError("File too large (max 10 MB)")

    storage = get_media_storage()
    if not storage:
        raise RuntimeError("S3 storage is not configured")

    stored_name, content_type = validate_upload_filename(original_filename)
    s3_key = build_s3_key(stored_name)
    await storage.put(s3_key, body, content_type=content_type)
    logger.info("Uploaded game media s3://%s/%s", settings.S3_BUCKET, s3_key)
    return stored_name, s3_key, content_type, build_public_url(stored_name)


async def fetch_media_bytes(filename: str) -> tuple[bytes, str] | None:
    if not validate_public_filename(filename):
        return None
    storage = get_media_storage()
    if not storage:
        return None
    s3_key = build_s3_key(filename)
    body = await storage.get_bytes(s3_key)
    if body is None:
        return None
    return body, guess_content_type(filename)


async def delete_media_file(s3_key: str) -> None:
    storage = get_media_storage()
    if not storage:
        raise RuntimeError("S3 storage is not configured")
    await storage.delete_object(s3_key)
