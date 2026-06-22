"""Доступ к S3-хранилищу (как в vk-bot)."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import settings

_storage = None


def get_storage():
    global _storage
    if _storage is not None:
        return _storage
    if not getattr(settings, "S3_BUCKET", None) or not getattr(settings, "S3_ACCESS_KEY", None):
        return None
    try:
        from shared_storage import get_storage as _get_s3

        _storage = _get_s3(
            bucket=settings.S3_BUCKET,
            endpoint_url=getattr(settings, "S3_ENDPOINT_URL", None) or None,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
            use_ssl=getattr(settings, "S3_USE_SSL", False),
        )
        return _storage
    except Exception:
        return None
