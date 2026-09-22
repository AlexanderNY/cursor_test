"""Optional S3 storage — returns None if not configured (local disk fallback)."""
from __future__ import annotations

from config import settings

_storage = None


def get_storage():
    global _storage
    if _storage is not None:
        return _storage
    if not settings.S3_BUCKET or not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
        return None
    # Optional: MinIO not required for 9to18 independence
    return None
