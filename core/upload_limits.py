"""Bounded UploadFile reads to prevent memory / disk DoS."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, UploadFile

_CHUNK = 64 * 1024


def _format_limit(max_bytes: int) -> str:
    if max_bytes >= 1024 * 1024:
        mb = max_bytes / (1024 * 1024)
        return f"{mb:g} MiB"
    if max_bytes >= 1024:
        return f"{max_bytes // 1024} KiB"
    return f"{max_bytes} B"


def _default_image_limit() -> int:
    from config import settings

    return int(settings.MAX_UPLOAD_IMAGE_BYTES)


def _default_files_limit() -> int:
    from config import settings

    return int(settings.MAX_UPLOAD_FILES_PER_REQUEST)


async def read_upload_limited(
    upload: UploadFile,
    *,
    max_bytes: Optional[int] = None,
    label: str = "File",
) -> bytes:
    """Read upload in chunks; raise HTTP 413 if over max_bytes.

    Prefer this over ``await upload.read()`` which buffers the whole body.
    """
    limit = int(max_bytes if max_bytes is not None else _default_image_limit())
    if limit <= 0:
        raise HTTPException(status_code=500, detail="Upload limit misconfigured")

    declared = getattr(upload, "size", None)
    if isinstance(declared, int) and declared > limit:
        raise HTTPException(
            status_code=413,
            detail=f"{label} too large (max {_format_limit(limit)})",
        )

    buf = bytearray()
    while True:
        chunk = await upload.read(_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > limit:
            try:
                await upload.close()
            except Exception:
                pass
            raise HTTPException(
                status_code=413,
                detail=f"{label} too large (max {_format_limit(limit)})",
            )
    return bytes(buf)


def enforce_upload_count(
    files: list,
    *,
    max_files: Optional[int] = None,
    label: str = "files",
) -> None:
    limit = int(max_files if max_files is not None else _default_files_limit())
    count = sum(1 for f in files if f is not None and getattr(f, "filename", None))
    if count > limit:
        raise HTTPException(
            status_code=413,
            detail=f"Too many {label} (max {limit})",
        )
