"""S3/MinIO storage with local disk fallback for resume exports."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from config import settings

logger = logging.getLogger(__name__)

LOCAL_EXPORT_ROOT = Path("uploads/resume/exports")


class ResumeStorage:
    """put_bytes + public/local download URL helpers."""

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
                    region_name=(settings.S3_REGION or "us-east-1").strip() or "us-east-1",
                    use_ssl=bool(settings.S3_USE_SSL),
                    config=Config(signature_version="s3v4"),
                )
            except Exception:
                logger.exception("Failed to init S3 client; using local disk")
                self._s3 = None

    @property
    def uses_s3(self) -> bool:
        return self._s3 is not None

    async def put_bytes(self, key: str, data: bytes, content_type: str) -> str:
        if self._s3 is not None:
            await __import__("asyncio").to_thread(
                self._s3.put_object,
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return f"s3:{key}"

        path = LOCAL_EXPORT_ROOT / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await __import__("asyncio").to_thread(path.write_bytes, data)
        return f"local:{key}"

    def presign_get(self, key: str, *, expires_seconds: int = 3600) -> Optional[str]:
        if self._s3 is None:
            return None
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def local_path(self, key: str) -> Path:
        return LOCAL_EXPORT_ROOT / key

    def read_local(self, key: str) -> Optional[bytes]:
        path = self.local_path(key)
        if not path.is_file():
            return None
        return path.read_bytes()


_storage: Optional[ResumeStorage] = None


def get_resume_storage() -> ResumeStorage:
    global _storage
    if _storage is None:
        _storage = ResumeStorage()
    return _storage


def safe_filename(name: str, ext: str) -> str:
    base = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in name).strip()
    base = base.replace(" ", "_")[:80] or "resume"
    return f"{base}.{ext.lstrip('.')}"


def build_api_file_url(file_id: str) -> str:
    return f"/api/resume/files/{quote(str(file_id))}"


def expires_iso(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
