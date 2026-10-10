"""S3/MinIO storage with local-disk fallback for site profile photos."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class SiteStorage:
    """put / get_bytes for profile photos (same S3 env as resume-api)."""

    def __init__(self) -> None:
        self._s3 = None
        self._bucket = (settings.S3_BUCKET or "").strip()
        if (
            self._bucket
            and (settings.S3_ACCESS_KEY or "").strip()
            and (settings.S3_SECRET_KEY or "").strip()
        ):
            try:
                import boto3
                from botocore.client import Config

                self._s3 = boto3.client(
                    "s3",
                    endpoint_url=(settings.S3_ENDPOINT_URL or "").strip() or None,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    region_name=(settings.S3_REGION or "us-east-1").strip()
                    or "us-east-1",
                    use_ssl=bool(settings.S3_USE_SSL),
                    config=Config(signature_version="s3v4"),
                )
            except Exception:
                logger.exception("Failed to init S3 client; photos use local disk")
                self._s3 = None

    @property
    def uses_s3(self) -> bool:
        return self._s3 is not None

    async def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        if self._s3 is None:
            raise RuntimeError("S3 storage is not configured")
        await asyncio.to_thread(
            self._s3.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def get_bytes(self, key: str) -> Optional[bytes]:
        if self._s3 is None:
            return None
        try:
            response = await asyncio.to_thread(
                self._s3.get_object,
                Bucket=self._bucket,
                Key=key,
            )
            body = response["Body"]
            return await asyncio.to_thread(body.read)
        except Exception:
            logger.exception("S3 get_object failed for %s", key)
            return None

    # Alias used by older call sites
    async def get(self, key: str) -> Optional[bytes]:
        return await self.get_bytes(key)


_storage: Optional[SiteStorage] = None


def get_storage() -> Optional[SiteStorage]:
    """Return S3-backed storage when configured; otherwise None (local disk)."""
    global _storage
    if not (
        (settings.S3_BUCKET or "").strip()
        and (settings.S3_ACCESS_KEY or "").strip()
        and (settings.S3_SECRET_KEY or "").strip()
    ):
        return None
    if _storage is None:
        _storage = SiteStorage()
    if not _storage.uses_s3:
        return None
    return _storage
