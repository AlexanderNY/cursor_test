"""Роутер голосований roadmap («Что далее»)."""

from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from schemas import (
    RoadmapItem,
    RoadmapItemCreate,
    RoadmapItemUpdate,
    RoadmapListResponse,
    RoadmapVoteResponse,
)
from services.roadmap_service import roadmap_service

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


def _require_user_id(x_user_id: Optional[str]) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid user ID") from exc


def _require_admin(x_user_role: Optional[str]) -> None:
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage roadmap items")


@router.get("", response_model=RoadmapListResponse)
async def list_roadmap(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> RoadmapListResponse:
    """Список пунктов roadmap. Неактивные видит только admin."""
    user_id = _require_user_id(x_user_id)
    include_inactive = x_user_role == "admin"
    return await roadmap_service.list_items(user_id, include_inactive=include_inactive)


@router.post("", response_model=RoadmapItem)
async def create_roadmap_item(
    payload: RoadmapItemCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> RoadmapItem:
    """Создаёт пункт roadmap. Только admin."""
    user_id = _require_user_id(x_user_id)
    _require_admin(x_user_role)
    return await roadmap_service.create_item(payload, created_by=user_id)


@router.patch("/{item_id}", response_model=RoadmapItem)
async def update_roadmap_item(
    item_id: int,
    payload: RoadmapItemUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> RoadmapItem:
    """Обновляет пункт roadmap. Только admin."""
    _require_user_id(x_user_id)
    _require_admin(x_user_role)
    return await roadmap_service.update_item(item_id, payload)


@router.delete("/{item_id}")
async def delete_roadmap_item(
    item_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict:
    """Удаляет пункт roadmap и его голоса. Только admin."""
    _require_user_id(x_user_id)
    _require_admin(x_user_role)
    return await roadmap_service.delete_item(item_id)


@router.post("/{item_id}/vote", response_model=RoadmapVoteResponse)
async def toggle_roadmap_vote(
    item_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> RoadmapVoteResponse:
    """Toggle голоса текущего пользователя за пункт."""
    user_id = _require_user_id(x_user_id)
    return await roadmap_service.toggle_vote(item_id, user_id)
