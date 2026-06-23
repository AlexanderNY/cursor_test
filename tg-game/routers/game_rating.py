"""Публичный рейтинг игры."""

from __future__ import annotations

from fastapi import APIRouter, Query

from schemas_game import LeaderboardEntryOut
from services.rating_service import get_leaderboard

router = APIRouter(tags=["Game"])


@router.get("/rating", response_model=list[LeaderboardEntryOut])
async def leaderboard(limit: int = Query(default=20, ge=1, le=100)) -> list[LeaderboardEntryOut]:
    rows = await get_leaderboard(limit=limit)
    return [LeaderboardEntryOut(**r) for r in rows]
