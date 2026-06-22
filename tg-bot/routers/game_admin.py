"""Админ CRUD: режимы, вопросы, варианты ответов."""

from __future__ import annotations

from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException

from deps_game_admin import verify_game_admin_token
from schemas_game import (
    GameModeCreate,
    GameModeOut,
    GameModeUpdate,
    GameQuestionCreate,
    GameQuestionOptionsReplace,
    GameQuestionOut,
    GameQuestionUpdate,
)
from services.game_repository import game_repository

router = APIRouter(prefix="/admin", tags=["Game Admin"])


@router.post("/modes", response_model=GameModeOut, dependencies=[Depends(verify_game_admin_token)])
async def create_mode(body: GameModeCreate) -> GameModeOut:
    try:
        mid = await game_repository.admin_create_mode(
            code=body.code.strip(),
            title=body.title.strip(),
            questions_per_game=body.questions_per_game,
            is_active=body.is_active,
        )
    except psycopg2.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Mode code already exists") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    row = await game_repository.get_mode(mid)
    if not row:
        raise HTTPException(status_code=500, detail="Mode not found after create")
    return GameModeOut(
        id=row.id,
        code=row.code,
        title=row.title,
        is_active=row.is_active,
        questions_per_game=row.questions_per_game,
    )


@router.get("/modes", response_model=list[GameModeOut], dependencies=[Depends(verify_game_admin_token)])
async def list_modes(include_inactive: bool = True) -> list[GameModeOut]:
    rows = await game_repository.admin_list_modes(include_inactive=include_inactive)
    return [
        GameModeOut(
            id=r.id,
            code=r.code,
            title=r.title,
            is_active=r.is_active,
            questions_per_game=r.questions_per_game,
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
    )
    row = await game_repository.get_mode(mode_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mode not found")
    return GameModeOut(
        id=row.id,
        code=row.code,
        title=row.title,
        is_active=row.is_active,
        questions_per_game=row.questions_per_game,
    )


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
