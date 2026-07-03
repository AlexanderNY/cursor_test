"""Публичная раздача медиафайлов опросов (для Telegram и UI preview)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from services.media_storage import fetch_media_bytes, validate_public_filename

router = APIRouter(tags=["Game Media Public"])


@router.get("/media/{filename}")
@router.head("/media/{filename}")
async def get_media_file(filename: str, request: Request) -> Response:
    if not validate_public_filename(filename):
        raise HTTPException(status_code=404, detail="Not found")

    result = await fetch_media_bytes(filename)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")

    body, content_type = result
    return Response(
        content=b"" if request.method == "HEAD" else body,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
