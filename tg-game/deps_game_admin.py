"""Проверка доступа к админ-API игры."""

from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException

from config import settings


def verify_game_admin_token(
    x_game_admin_token: Optional[str] = Header(default=None, alias="X-Game-Admin-Token"),
) -> None:
    expected = (settings.GAME_ADMIN_API_TOKEN or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="GAME_ADMIN_API_TOKEN is not configured",
        )
    if not x_game_admin_token or x_game_admin_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Game-Admin-Token")
