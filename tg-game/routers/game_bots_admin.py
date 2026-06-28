"""Админ CRUD ботов Telegram-игры."""

from __future__ import annotations

from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException

from deps_game_admin import verify_game_admin_token
from schemas_game import GameBotCreate, GameBotOut, GameBotUpdate
from services.bot_manager import is_bot_polling, reload_all_bots
from services.bot_telegram import fetch_bot_info, mask_bot_token
from services.game_repository import game_repository

router = APIRouter(prefix="/admin/bots", tags=["Game Bots Admin"])


def _bot_to_out(row: dict) -> GameBotOut:
    return GameBotOut(
        id=int(row["id"]),
        name=str(row["name"]),
        username=row.get("username"),
        token=str(row["token"]),
        token_masked=mask_bot_token(str(row["token"])),
        is_active=bool(row["is_active"]),
        is_polling=is_bot_polling(int(row["id"])),
        created_at=row.get("created_at"),
    )


@router.get("", response_model=list[GameBotOut], dependencies=[Depends(verify_game_admin_token)])
async def list_bots() -> list[GameBotOut]:
    rows = await game_repository.admin_list_bots()
    return [_bot_to_out(row) for row in rows]


@router.post("", response_model=GameBotOut, dependencies=[Depends(verify_game_admin_token)])
async def create_bot(body: GameBotCreate) -> GameBotOut:
    token = body.token.strip()
    try:
        info = await fetch_bot_info(token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    username = info.get("username")
    name = body.name.strip() or (f"@{username}" if username else "Telegram Bot")
    try:
        bot_id = await game_repository.admin_create_bot(
            name=name,
            token=token,
            username=username,
            is_active=body.is_active,
        )
    except psycopg2.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Bot token already exists") from exc

    await reload_all_bots()
    row = await game_repository.get_bot(bot_id)
    if not row:
        raise HTTPException(status_code=500, detail="Bot not found after create")
    return _bot_to_out(
        {
            "id": row.id,
            "name": row.name,
            "token": row.token,
            "username": row.username,
            "is_active": row.is_active,
            "created_at": None,
        }
    )


@router.patch("/{bot_id}", response_model=GameBotOut, dependencies=[Depends(verify_game_admin_token)])
async def update_bot(bot_id: int, body: GameBotUpdate) -> GameBotOut:
    row = await game_repository.get_bot(bot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Bot not found")

    new_token = body.token.strip() if body.token else None
    username: Optional[str] = None
    if new_token:
        try:
            info = await fetch_bot_info(new_token)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        username = info.get("username")

    try:
        await game_repository.admin_update_bot(
            bot_id,
            name=body.name.strip() if body.name else None,
            token=new_token,
            username=username,
            is_active=body.is_active,
        )
    except psycopg2.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Bot token already exists") from exc

    await reload_all_bots()
    updated = await game_repository.get_bot(bot_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Bot not found")
    return _bot_to_out(
        {
            "id": updated.id,
            "name": updated.name,
            "token": updated.token,
            "username": updated.username,
            "is_active": updated.is_active,
            "created_at": None,
        }
    )


@router.delete("/{bot_id}", dependencies=[Depends(verify_game_admin_token)])
async def delete_bot(bot_id: int) -> dict[str, str]:
    row = await game_repository.get_bot(bot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Bot not found")
    try:
        deleted = await game_repository.admin_delete_bot(bot_id)
    except psycopg2.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Bot has linked game modes and cannot be deleted",
        ) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Bot not found")
    await reload_all_bots()
    return {"status": "ok"}
