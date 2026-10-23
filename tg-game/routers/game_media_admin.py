"""Админ CRUD медиатеки опросов."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from deps_game_admin import verify_game_admin_token
from schemas_game import GameMediaOut, GameMediaUpdate
from services.media_repository import media_repository
from services.media_storage import delete_media_file, upload_media_file

router = APIRouter(prefix="/admin", tags=["Game Media Admin"])

_MAX_MEDIA_BYTES = 8 * 1024 * 1024
_READ_CHUNK = 64 * 1024


async def _read_media_limited(upload: UploadFile) -> bytes:
    buf = bytearray()
    while True:
        chunk = await upload.read(_READ_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > _MAX_MEDIA_BYTES:
            raise HTTPException(status_code=413, detail="File too large (max 8 MB)")
    return bytes(buf)


@router.get("/media", response_model=list[GameMediaOut], dependencies=[Depends(verify_game_admin_token)])
async def list_media() -> list[GameMediaOut]:
    rows = await media_repository.list_all()
    return [GameMediaOut(**media_repository.to_dict(r)) for r in rows]


@router.post("/media", response_model=GameMediaOut, dependencies=[Depends(verify_game_admin_token)])
async def upload_media(
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
) -> GameMediaOut:
    body = await _read_media_limited(file)
    original = file.filename
    try:
        stored_name, s3_key, content_type, _public_url = await upload_media_file(
            body=body,
            original_filename=original,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    default_title = (title or "").strip() or (Path(original or stored_name).stem if original else stored_name)
    row = await media_repository.create(
        filename=stored_name,
        s3_key=s3_key,
        original_filename=original,
        title=default_title,
        description=(description or "").strip() or None,
        content_type=content_type,
        size_bytes=len(body),
    )
    return GameMediaOut(**media_repository.to_dict(row))


@router.patch(
    "/media/{asset_id}",
    response_model=GameMediaOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def update_media(asset_id: int, body: GameMediaUpdate) -> GameMediaOut:
    row = await media_repository.update(
        asset_id,
        title=body.title,
        description=body.description,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return GameMediaOut(**media_repository.to_dict(row))


@router.delete(
    "/media/{asset_id}",
    dependencies=[Depends(verify_game_admin_token)],
)
async def delete_media(asset_id: int) -> dict[str, str]:
    s3_key = await media_repository.delete(asset_id)
    if not s3_key:
        raise HTTPException(status_code=404, detail="Media asset not found")
    try:
        await delete_media_file(s3_key)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"status": "ok"}
