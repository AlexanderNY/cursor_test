"""Роутер для рабочих групп."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional

from schemas import (
    GroupCreate,
    GroupCreateAdmin,
    GroupUpdate,
    GroupResponse,
    GroupMemberResponse,
    AddMemberRequest,
    CreateInviteRequest,
    GroupInviteResponse,
    InviteActionResponse,
    InvitePeekResponse,
    AcceptInviteResponse,
)
from services import group_service
from dependencies import get_current_user, get_admin_user


router = APIRouter(prefix="/groups", tags=["groups"])


def _invite_to_response(inv: Dict) -> GroupInviteResponse:
    return GroupInviteResponse(
        id=inv["id"],
        group_id=inv["group_id"],
        email=inv.get("email"),
        role_in_group=inv["role_in_group"],
        token=inv["token"],
        invited_by_user_id=inv["invited_by_user_id"],
        status=inv["status"],
        expires_at=inv["expires_at"],
        created_at=inv["created_at"],
        group_name=inv.get("group_name"),
        invite_path=f"/invite/{inv['token']}",
    )


def _group_to_response(g: Dict, with_members: bool = True) -> GroupResponse:
    members = None
    if with_members and g.get("members") is not None:
        members = [
            GroupMemberResponse(
                user_id=m["user_id"],
                username=m["username"],
                email=m["email"],
                tariff=m["tariff"],
                role_in_group=m["role_in_group"],
                joined_at=m["joined_at"],
            )
            for m in g["members"]
        ]
    return GroupResponse(
        id=g["id"],
        name=g["name"],
        description=g.get("description"),
        created_at=g["created_at"],
        created_by_user_id=g.get("created_by_user_id"),
        role_in_group=g.get("role_in_group"),
        members=members,
    )


@router.get("/my", response_model=GroupResponse)
async def get_my_group(current_user: Dict = Depends(get_current_user)) -> GroupResponse:
    """Получение «первой» группы пользователя (по дате вступления)."""
    group = await group_service.get_my_group(
        current_user["id"],
        current_user.get("role", "user"),
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not in any group",
        )
    return _group_to_response(group, with_members=bool(group.get("members")))


@router.post("/admin", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group_as_admin(
    body: GroupCreateAdmin,
    admin_user: Dict = Depends(get_admin_user),
) -> GroupResponse:
    """Создание пустой группы с названием и описанием (только admin). Участников добавьте отдельно."""
    try:
        g = await group_service.create_group_by_admin(
            body.name,
            body.description,
            admin_user["id"],
        )
        return _group_to_response(g, with_members=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    current_user: Dict = Depends(get_current_user),
) -> GroupResponse:
    """Создание группы (создатель становится manager)."""
    try:
        group = await group_service.create_group(
            current_user["id"],
            body.name,
            current_user.get("role", "user"),
            description=body.description,
        )
        full = await group_service.get_group_by_id(group["id"], include_members=True)
        if not full:
            raise HTTPException(status_code=500, detail="Failed to load group")
        full["role_in_group"] = "admin"
        return _group_to_response(full, with_members=True)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    body: GroupUpdate,
    current_user: Dict = Depends(get_current_user),
) -> GroupResponse:
    """Обновление названия и/или описания группы."""
    try:
        await group_service.update_group(
            group_id,
            current_user["id"],
            current_user.get("role", "user"),
            name=body.name,
            description=body.description,
        )
        full_group = await group_service.get_group_by_id(group_id, include_members=True)
        if not full_group:
            raise HTTPException(status_code=404, detail="Group not found")
        membership = await group_service.get_membership_in_group(current_user["id"], group_id)
        full_group["role_in_group"] = membership.get("role_in_group") if membership else None
        return _group_to_response(full_group, with_members=True)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: int,
    body: AddMemberRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Добавление участника по email. Первый участник пустой группы — только manager."""
    try:
        member = await group_service.add_member_by_email(
            group_id,
            body.email,
            current_user["id"],
            current_user.get("role", "user"),
            role_in_group=body.role_in_group,
        )
        return member
    except group_service.TeamSeatLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": str(e),
                "resource": e.resource,
                "limit": e.limit,
                "used": e.used,
                "tariff": e.tariff,
                "upgrade_url": "/pricing",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: int,
    user_id: int,
    current_user: Dict = Depends(get_current_user),
) -> None:
    """Удаление участника из группы."""
    try:
        await group_service.remove_member(
            group_id,
            user_id,
            current_user["id"],
            current_user.get("role", "user"),
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-member-ids")
async def get_my_group_member_ids(
    current_user: Dict = Depends(get_current_user),
    group_id: Optional[int] = Query(
        None,
        description="ID группы; если не указан — первая группа пользователя",
    ),
) -> List[int]:
    """Список user_id участников группы (manager группы или admin)."""
    memberships = await group_service.get_user_group_memberships(current_user["id"])
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not in any group",
        )
    target_gid = group_id if group_id is not None else memberships[0]["group_id"]
    m = await group_service.get_membership_in_group(current_user["id"], target_gid)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this group",
        )
    if m["role_in_group"] not in ("manager", "admin") and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admin can get member ids",
        )
    return await group_service.get_group_member_user_ids(target_gid)


@router.get("/group-members-user-ids/{group_id}")
async def get_group_member_user_ids_for_statistics(
    group_id: int,
    current_user: Dict = Depends(get_current_user),
) -> List[int]:
    """Список user_id участников группы (manager этой группы или admin)."""
    membership = await group_service.get_membership_in_group(current_user["id"], group_id)
    if current_user.get("role") != "admin":
        if not membership or membership["role_in_group"] not in ("manager", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admin or platform admin can get member ids",
            )
    ids = await group_service.get_group_member_user_ids(group_id)
    return ids


@router.get("", response_model=List[GroupResponse])
async def get_all_groups(admin_user: Dict = Depends(get_admin_user)) -> List[GroupResponse]:
    """Список всех групп с участниками. Только admin."""
    groups = await group_service.get_all_groups_with_members()
    return [_group_to_response(g, with_members=True) for g in groups]


@router.post("/{group_id}/invites", response_model=InviteActionResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    group_id: int,
    body: CreateInviteRequest,
    current_user: Dict = Depends(get_current_user),
) -> InviteActionResponse:
    """Создать invite. Если email уже в системе — сразу добавить; иначе ссылка."""
    try:
        result = await group_service.create_invite(
            group_id,
            current_user["id"],
            current_user.get("role", "user"),
            email=body.email,
            role_in_group=body.role_in_group,
            expires_days=body.expires_days,
        )
        member = None
        if result.get("member"):
            m = result["member"]
            member = GroupMemberResponse(
                user_id=m["user_id"],
                username=m["username"],
                email=m["email"],
                tariff=m.get("tariff", "free"),
                role_in_group=m["role_in_group"],
                joined_at=m["joined_at"],
            )
        invite = _invite_to_response(result["invite"]) if result.get("invite") else None
        return InviteActionResponse(
            status=result["status"],
            group_name=result.get("group_name"),
            member=member,
            invite=invite,
        )
    except group_service.TeamSeatLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": str(e),
                "resource": e.resource,
                "limit": e.limit,
                "used": e.used,
                "tariff": e.tariff,
                "upgrade_url": "/pricing",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{group_id}/invites", response_model=List[GroupInviteResponse])
async def list_invites(
    group_id: int,
    current_user: Dict = Depends(get_current_user),
) -> List[GroupInviteResponse]:
    try:
        invites = await group_service.list_pending_invites(
            group_id, current_user["id"], current_user.get("role", "user")
        )
        return [_invite_to_response(i) for i in invites]
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{group_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    group_id: int,
    invite_id: int,
    current_user: Dict = Depends(get_current_user),
) -> None:
    try:
        await group_service.revoke_invite(
            group_id, invite_id, current_user["id"], current_user.get("role", "user")
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/invites/{token}", response_model=InvitePeekResponse)
async def peek_invite(token: str) -> InvitePeekResponse:
    """Публичный просмотр invite (без auth)."""
    invite = await group_service.get_invite_by_token(token)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    return InvitePeekResponse(
        group_name=invite.get("group_name") or "Team",
        email=invite.get("email"),
        role_in_group=invite["role_in_group"],
        status=invite["status"],
        expires_at=invite["expires_at"],
    )


@router.post("/invites/{token}/accept", response_model=AcceptInviteResponse)
async def accept_invite(
    token: str,
    current_user: Dict = Depends(get_current_user),
) -> AcceptInviteResponse:
    """Принять invite (авторизованный пользователь)."""
    try:
        result = await group_service.accept_invite(
            token, current_user["id"], user_email=current_user.get("email")
        )
        return AcceptInviteResponse(**result)
    except group_service.TeamSeatLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": str(e),
                "resource": e.resource,
                "limit": e.limit,
                "used": e.used,
                "tariff": e.tariff,
                "upgrade_url": "/pricing",
            },
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
