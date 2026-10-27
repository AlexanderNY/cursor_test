"""Форум: беседы Workspace и общие ветки платформы."""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query

from schemas import (
    ForumListResponse,
    ForumPost,
    ForumPostCreate,
    ForumThreadCreate,
    ForumThreadDetail,
    ForumThreadUpdate,
    ForumVoteResponse,
)
from services.forum_policy import UNKNOWN_KIND, UNKNOWN_SCOPE, parse_kind_filter, parse_scope
from services.forum_service import forum_service

router = APIRouter(prefix="/forum", tags=["Forum"])


def _require_user_id(x_user_id: Optional[str]) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid user ID") from exc


def _is_platform_admin(x_user_role: Optional[str]) -> bool:
    return (x_user_role or "").lower() == "admin"


@router.get("/threads", response_model=ForumListResponse)
async def list_threads(
    scope: str = Query(default="platform"),
    kind: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> ForumListResponse:
    """Список веток. scope=workspace — активная команда, scope=platform — общие."""
    user_id = _require_user_id(x_user_id)
    parsed_scope = parse_scope(scope)
    if parsed_scope is None:
        raise HTTPException(status_code=400, detail=UNKNOWN_SCOPE)
    kind_ok, parsed_kind = parse_kind_filter(kind)
    if not kind_ok:
        raise HTTPException(status_code=400, detail=UNKNOWN_KIND)
    return await forum_service.list_threads(
        user_id,
        scope=parsed_scope,
        kind=parsed_kind,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.post("/threads", response_model=ForumThreadDetail)
async def create_thread(
    payload: ForumThreadCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> ForumThreadDetail:
    """Открывает ветку в активном Workspace или на платформе."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.create_thread(
        user_id,
        payload,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.get("/threads/{thread_id}", response_model=ForumThreadDetail)
async def get_thread(
    thread_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> ForumThreadDetail:
    """Ветка и ответы. Чужая команда отвечает 404."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.get_thread(
        user_id,
        thread_id,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.patch("/threads/{thread_id}", response_model=ForumThreadDetail)
async def update_thread(
    thread_id: int,
    payload: ForumThreadUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> ForumThreadDetail:
    """Закрывает или открывает ветку. Автор, владелец Workspace или admin."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.set_closed(
        user_id,
        thread_id,
        payload,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict:
    """Удаляет ветку вместе с ответами и голосами."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.delete_thread(
        user_id,
        thread_id,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.post("/threads/{thread_id}/posts", response_model=ForumPost)
async def create_post(
    thread_id: int,
    payload: ForumPostCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> ForumPost:
    """Ответ в открытой ветке."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.add_post(
        user_id,
        thread_id,
        payload,
        is_platform_admin=_is_platform_admin(x_user_role),
    )


@router.post("/threads/{thread_id}/vote", response_model=ForumVoteResponse)
async def toggle_vote(
    thread_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> ForumVoteResponse:
    """Toggle голоса. Только ветки типа «идея»."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.toggle_vote(user_id, thread_id)


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict:
    """Удаляет ответ. Автор ответа, владелец Workspace или admin."""
    user_id = _require_user_id(x_user_id)
    return await forum_service.delete_post(
        user_id,
        post_id,
        is_platform_admin=_is_platform_admin(x_user_role),
    )
