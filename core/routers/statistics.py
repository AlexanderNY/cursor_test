"""Роутер для получения статистики."""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from services.statistics_service import statistics_service
from schemas import StatisticsResponse, UserStatisticsResponse
from dependencies import get_current_user, get_admin_user
from typing import Dict, List
import httpx
from config import settings


router = APIRouter(tags=["Statistics"])


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получает статистику постов по всем платформам.
    
    Returns:
        StatisticsResponse: Статистика по платформам
    """
    services = await statistics_service.get_statistics()
    return {"services": services}


def _merge_users_with_stats(
    posts_stats: List[Dict],
    users_dict: Dict[int, Dict],
) -> List[Dict]:
    """Объединяет статистику постов с данными пользователей."""
    result = []
    for stat in posts_stats:
        user_id = stat["user_id"]
        user_info = users_dict.get(user_id, {})
        result.append({
            "user_id": user_id,
            "username": user_info.get("username", f"User {user_id}"),
            "email": user_info.get("email", ""),
            "role": user_info.get("role", "guest"),
            "total_posts": stat["total_posts"],
            "collected_posts": stat["collected_posts"],
            "processed_posts": stat["processed_posts"],
            "published_posts": stat["published_posts"]
        })
    return result


@router.get("/users-statistics", response_model=UserStatisticsResponse)
async def get_users_statistics(
    request: Request,
    admin_user: Dict = Depends(get_admin_user),
):
    """Получает статистику по всем пользователям. Только admin."""
    posts_stats = await statistics_service.get_users_statistics()
    authorization = request.headers.get("Authorization", "")
    headers = {"Authorization": authorization} if authorization else {}
    try:
        async with httpx.AsyncClient() as client:
            auth_url = f"{settings.API_GATEWAY_URL}/auth/users"
            response = await client.get(auth_url, headers=headers)
            response.raise_for_status()
            users_data = response.json()
    except Exception:
        users_data = []
    users_dict = {
        user.get("id", user.get("user_id")): user
        for user in users_data
        if user.get("id") or user.get("user_id")
    }
    result = _merge_users_with_stats(posts_stats, users_dict)
    return {"users": result}


@router.get("/group-statistics", response_model=UserStatisticsResponse)
async def get_group_statistics(request: Request, current_user: Dict = Depends(get_current_user)):
    """Получает статистику только по пользователям своей группы. Только менеджер группы или admin."""
    if current_user.get("role") not in ("manager", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group manager or admin can view group statistics",
        )
    authorization = request.headers.get("Authorization", "")
    headers = {"Authorization": authorization} if authorization else {}
    try:
        async with httpx.AsyncClient() as client:
            auth_url = f"{settings.AUTH_SERVICE_URL}/groups/my"
            response = await client.get(auth_url, headers=headers)
            if response.status_code == 404:
                return {"users": []}
            response.raise_for_status()
            group = response.json()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot load group",
        )
    members = group.get("members") or []
    if not members:
        return {"users": []}
    user_ids = [m["user_id"] for m in members]
    users_dict = {m["user_id"]: m for m in members}
    for u in users_dict.values():
        if "role" not in u:
            u["role"] = u.get("role_in_group", "author")
    posts_stats = await statistics_service.get_users_statistics(user_ids=user_ids)
    result = _merge_users_with_stats(posts_stats, users_dict)
    return {"users": result}
