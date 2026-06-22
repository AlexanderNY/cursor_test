from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import PlainTextResponse
from schemas import (
    UserProfile,
    UserProfileUpdate,
    AdminUserUpdate,
    RoleTariffHistoryEntry,
    user_profile_from_user_dict,
    AdminAuditLogEntry,
)
from services.auth_service import (
    update_user_profile,
    get_all_users,
    update_user_role_tariff,
    get_user_role_tariff_history,
    export_users_csv_rows,
)
from services.admin_audit_service import get_admin_audit_log
from services import group_service
from utils.exceptions import UserAlreadyExistsError, UserNotFoundError
from dependencies import get_current_user, get_admin_user
from typing import Dict, List


router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: Dict = Depends(get_current_user)) -> UserProfile:
    """Получение профиля текущего пользователя."""
    memberships = await group_service.get_user_group_memberships(current_user["id"])
    return user_profile_from_user_dict(current_user, memberships)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: Dict = Depends(get_current_user)
) -> UserProfile:
    """Обновление профиля текущего пользователя."""
    try:
        updated_user = await update_user_profile(
            user_id=current_user["id"],
            username=profile_update.username,
            email=profile_update.email
        )
        memberships = await group_service.get_user_group_memberships(updated_user["id"])
        return user_profile_from_user_dict(updated_user, memberships)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/users", response_model=List[UserProfile])
async def get_users(
    admin_user: Dict = Depends(get_admin_user),
    tariff: str | None = Query(None, description="Фильтр по тарифу"),
    subscription_status: str | None = Query(
        None,
        description="Статус подписки или __null__ если не задан",
    ),
) -> List[UserProfile]:
    """Получение списка пользователей с фильтрами (только для администраторов)."""
    try:
        users = await get_all_users(tariff=tariff, subscription_status=subscription_status)
        return [user_profile_from_user_dict(user, None) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.get("/users/export", response_class=PlainTextResponse)
async def export_users(
    admin_user: Dict = Depends(get_admin_user),
    tariff: str | None = Query(None),
    subscription_status: str | None = Query(None),
) -> PlainTextResponse:
    """Экспорт пользователей в CSV (фильтры как у GET /users)."""
    users = await get_all_users(tariff=tariff, subscription_status=subscription_status)
    csv_text = export_users_csv_rows(users)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="users_export.csv"'},
    )


@router.patch("/users/{user_id}", response_model=UserProfile)
async def update_user_role_and_tariff(
    user_id: int,
    body: AdminUserUpdate,
    admin_user: Dict = Depends(get_admin_user)
) -> UserProfile:
    """Изменение роли и/или тарифа пользователя (только для администраторов)."""
    if body.is_blocked is True and admin_user.get("id") == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block your own account",
        )
    try:
        updated_user = await update_user_role_tariff(
            user_id=user_id,
            role=body.role,
            tariff=body.tariff,
            is_blocked=body.is_blocked,
            changed_by_user_id=admin_user.get("id"),
        )
        return user_profile_from_user_dict(updated_user, None)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/users/{user_id}/role-tariff-history", response_model=List[RoleTariffHistoryEntry])
async def get_role_tariff_history(
    user_id: int,
    current_user: Dict = Depends(get_current_user),
) -> List[RoleTariffHistoryEntry]:
    """История изменений роли и тарифа. Админ — для любого user_id, иначе только свой."""
    is_admin = current_user.get("role") == "admin"
    if not is_admin and current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own history.",
        )
    entries = await get_user_role_tariff_history(user_id)
    return [
        RoleTariffHistoryEntry(
            id=e["id"],
            user_id=e["user_id"],
            changed_at=e["changed_at"],
            changed_by_user_id=e.get("changed_by_user_id"),
            role_old=e.get("role_old"),
            role_new=e.get("role_new"),
            tariff_old=e.get("tariff_old"),
            tariff_new=e.get("tariff_new"),
        )
        for e in entries
    ]


@router.get("/admin/audit-log", response_model=List[AdminAuditLogEntry])
async def admin_audit_log(
    admin_user: Dict = Depends(get_admin_user),
    limit: int = Query(100, ge=1, le=500),
) -> List[AdminAuditLogEntry]:
    """Журнал действий администраторов."""
    rows = await get_admin_audit_log(limit=limit)
    return [
        AdminAuditLogEntry(
            id=r["id"],
            admin_user_id=r["admin_user_id"],
            action=r["action"],
            target_type=r["target_type"],
            target_id=r["target_id"],
            details_json=r["details_json"],
            created_at=r["created_at"],
        )
        for r in rows
    ]

