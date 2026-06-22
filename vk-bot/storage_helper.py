"""Доступ к единому S3-хранилищу. При отсутствии конфигурации возвращает None."""

import logging
import sys
from pathlib import Path
from typing import Optional

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import settings

logger = logging.getLogger(__name__)

_storage = None


def get_storage():
    global _storage
    if _storage is not None:
        return _storage
    if not getattr(settings, "S3_BUCKET", None) or not getattr(settings, "S3_ACCESS_KEY", None) or not getattr(settings, "S3_SECRET_KEY", None):
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


def put_bytes_sync(key: str, body: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
    """
    Синхронная загрузка объекта в S3 (boto3), без event loop — для потоков Selenium.

    Returns:
        Ключ объекта в бакете при успехе, иначе None.
    """
    if not body:
        return None
    bucket = getattr(settings, "S3_BUCKET", None) or ""
    access_key = getattr(settings, "S3_ACCESS_KEY", None) or ""
    secret_key = getattr(settings, "S3_SECRET_KEY", None) or ""
    if not bucket or not access_key or not secret_key:
        logger.debug("put_bytes_sync: S3 not configured, skip key=%s", key[:80])
        return None
    key = key.lstrip("/")
    if not key:
        return None
    try:
        import boto3
    except ImportError:
        logger.warning("put_bytes_sync: boto3 not available")
        return None
    endpoint = getattr(settings, "S3_ENDPOINT_URL", None) or None
    client_kw: dict = {
        "region_name": "us-east-1",
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "use_ssl": bool(getattr(settings, "S3_USE_SSL", False)),
    }
    if endpoint:
        client_kw["endpoint_url"] = endpoint
    try:
        client = boto3.client("s3", **client_kw)
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        logger.info("put_bytes_sync: uploaded key=%s size=%s", key, len(body))
        return key
    except Exception as e:
        logger.warning("put_bytes_sync failed key=%s: %s", key[:120], e)
        return None
