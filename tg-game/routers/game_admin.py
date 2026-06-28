"""Админ CRUD: режимы, вопросы, варианты ответов."""

from __future__ import annotations

from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query

from deps_game_admin import verify_game_admin_token
from schemas_game import (
    GameModeCreate,
    GameModeOut,
    GameModeUpdate,
    GameQuestionCreate,
    GameQuestionDetailOut,
    GameQuestionOptionsReplace,
    GameQuestionOut,
    GameQuestionUpdate,
    GameSessionStatsOut,
    LeaderboardEntryOut,
)
from services.game_repository import game_repository
from services.media_storage import resolve_public_media_url
from services.rating_service import get_leaderboard

router = APIRouter(prefix="/admin", tags=["Game Admin"])


@router.post("/modes", response_model=GameModeOut, dependencies=[Depends(verify_game_admin_token)])
async def create_mode(body: GameModeCreate) -> GameModeOut:
    bot = await game_repository.get_bot(body.bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    try:
        mid = await game_repository.admin_create_mode(
            bot_id=body.bot_id,
            code=body.code.strip(),
            title=body.title.strip(),
            questions_per_game=body.questions_per_game,
            is_active=body.is_active,
            mode_type=body.mode_type,
        )
    except psycopg2.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Mode code already exists for this bot") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    row = await game_repository.get_mode(mid)
    if not row:
        raise HTTPException(status_code=500, detail="Mode not found after create")
    return GameModeOut(
        id=row.id,
        bot_id=row.bot_id or body.bot_id,
        code=row.code,
        title=row.title,
        is_active=row.is_active,
        questions_per_game=row.questions_per_game,
        mode_type=row.mode_type,  # type: ignore[arg-type]
    )


@router.get("/modes", response_model=list[GameModeOut], dependencies=[Depends(verify_game_admin_token)])
async def list_modes(
    include_inactive: bool = True,
    bot_id: Optional[int] = None,
) -> list[GameModeOut]:
    rows = await game_repository.admin_list_modes(include_inactive=include_inactive, bot_id=bot_id)
    return [
        GameModeOut(
            id=r.id,
            bot_id=r.bot_id or 0,
            code=r.code,
            title=r.title,
            is_active=r.is_active,
            questions_per_game=r.questions_per_game,
            mode_type=r.mode_type,  # type: ignore[arg-type]
        )
        for r in rows
    ]


@router.patch("/modes/{mode_id}", response_model=GameModeOut, dependencies=[Depends(verify_game_admin_token)])
async def update_mode(mode_id: int, body: GameModeUpdate) -> GameModeOut:
    await game_repository.admin_update_mode(
        mode_id,
        title=body.title,
        is_active=body.is_active,
        questions_per_game=body.questions_per_game,
        mode_type=body.mode_type,
    )
    row = await game_repository.get_mode(mode_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mode not found")
    return GameModeOut(
        id=row.id,
        bot_id=row.bot_id or 0,
        code=row.code,
        title=row.title,
        is_active=row.is_active,
        questions_per_game=row.questions_per_game,
        mode_type=row.mode_type,  # type: ignore[arg-type]
    )


@router.delete(
    "/modes/{mode_id}",
    dependencies=[Depends(verify_game_admin_token)],
)
async def delete_mode(mode_id: int) -> dict[str, str]:
    row = await game_repository.get_mode(mode_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mode not found")
    deleted = await game_repository.admin_delete_mode(mode_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mode not found")
    return {"status": "ok"}


@router.get(
    "/modes/{mode_id}/questions",
    response_model=list[GameQuestionOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def list_questions(mode_id: int) -> list[GameQuestionOut]:
    mode = await game_repository.get_mode(mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    rows = await game_repository.admin_list_questions(mode_id)
    return [GameQuestionOut(**r) for r in rows]


@router.post(
    "/questions",
    response_model=GameQuestionOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def create_question(body: GameQuestionCreate) -> GameQuestionOut:
    mode = await game_repository.get_mode(body.mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    opts = [
        {
            "option_index": o.option_index,
            "option_text": o.option_text,
            "is_correct": o.is_correct,
        }
        for o in body.options
    ]
    try:
        qid = await game_repository.admin_create_question_with_options(
            mode_id=body.mode_id,
            prompt_text=body.prompt_text,
            image_file_id=body.image_file_id,
            image_url=body.image_url,
            options=opts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    rows = await game_repository.admin_list_questions(body.mode_id)
    found: Optional[dict] = next((r for r in rows if r["id"] == qid), None)
    if not found:
        raise HTTPException(status_code=500, detail="Question not found after create")
    return GameQuestionOut(**found)


@router.get(
    "/questions/{question_id}",
    response_model=GameQuestionDetailOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def get_question(question_id: int) -> GameQuestionDetailOut:
    question, options = await game_repository.get_question_with_options(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    rows = await game_repository.admin_list_questions(question.mode_id)
    meta = next((r for r in rows if r["id"] == question_id), None)
    is_active = bool(meta["is_active"]) if meta else True

    return GameQuestionDetailOut(
        id=question.id,
        mode_id=question.mode_id,
        prompt_text=question.prompt_text,
        image_file_id=question.image_file_id,
        image_url=resolve_public_media_url(question.image_url),
        is_active=is_active,
        options=[
            {
                "id": o.id,
                "option_index": o.option_index,
                "option_text": o.option_text,
                "is_correct": o.is_correct,
            }
            for o in options
        ],
    )


@router.patch(
    "/questions/{question_id}",
    response_model=GameQuestionOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def update_question(question_id: int, body: GameQuestionUpdate) -> GameQuestionOut:
    q, _opts = await game_repository.get_question_with_options(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    await game_repository.admin_update_question(
        question_id,
        prompt_text=body.prompt_text,
        image_file_id=body.image_file_id,
        image_url=body.image_url,
        is_active=body.is_active,
    )
    rows = await game_repository.admin_list_questions(q.mode_id)
    found = next((r for r in rows if r["id"] == question_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Question not found")
    return GameQuestionOut(**found)


@router.put(
    "/questions/{question_id}/options",
    dependencies=[Depends(verify_game_admin_token)],
)
async def replace_options(question_id: int, body: GameQuestionOptionsReplace) -> dict[str, str]:
    q, _opts = await game_repository.get_question_with_options(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    opts = [
        {
            "option_index": o.option_index,
            "option_text": o.option_text,
            "is_correct": o.is_correct,
        }
        for o in body.options
    ]
    try:
        await game_repository.admin_replace_question_options(question_id, opts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"status": "ok"}


@router.delete(
    "/questions/{question_id}",
    dependencies=[Depends(verify_game_admin_token)],
)
async def delete_question(question_id: int) -> dict[str, str]:
    q, _opts = await game_repository.get_question_with_options(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    deleted = await game_repository.admin_delete_question(question_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"status": "ok"}


@router.get(
    "/rating",
    response_model=list[LeaderboardEntryOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def admin_leaderboard(limit: int = Query(default=50, ge=1, le=200)) -> list[LeaderboardEntryOut]:
    rows = await get_leaderboard(limit=limit)
    return [LeaderboardEntryOut(**r) for r in rows]


@router.get(
    "/sessions",
    response_model=list[GameSessionStatsOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def admin_completed_sessions(
    limit: int = Query(default=100, ge=1, le=500),
    mode_id: Optional[int] = None,
) -> list[GameSessionStatsOut]:
    rows = await game_repository.fetch_completed_sessions(limit=limit, mode_id=mode_id)
    return [GameSessionStatsOut(**r) for r in rows]
