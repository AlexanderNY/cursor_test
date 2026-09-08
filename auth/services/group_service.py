"""Сервис для работы с рабочими группами (пользователь может состоять в нескольких группах)."""

from typing import Dict, List, Optional, Tuple

from billing.plan_definitions import plan_limit
from database import get_db_connection


class TeamSeatLimitError(Exception):
    """Превышен лимит мест команды по тарифу владельца группы."""

    def __init__(self, *, limit: int, used: int, tariff: str) -> None:
        self.limit = limit
        self.used = used
        self.tariff = tariff
        self.resource = "max_team_seats"
        super().__init__(
            f"Team seat limit reached ({used}/{limit}) on {tariff} plan. Upgrade to add more members."
        )


async def _count_group_members(group_id: int) -> int:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM group_members WHERE group_id = %s",
                (group_id,),
            )
            row = await cur.fetchone()
    return int(row[0]) if row else 0


async def _count_owners_in_group(group_id: int) -> int:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM group_members
                WHERE group_id = %s AND role_in_group = 'owner'
                """,
                (group_id,),
            )
            row = await cur.fetchone()
    return int(row[0]) if row else 0


async def _count_managers_in_group(group_id: int) -> int:
    """Backward-compatible alias for owner count."""
    return await _count_owners_in_group(group_id)


async def _seat_budget_for_group(group_id: int) -> Tuple[int, str]:
    """Лимит seats по тарифу создателя группы (billing owner)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COALESCE(u.tariff, 'free')
                FROM groups g
                LEFT JOIN users u ON u.id = g.created_by_user_id
                WHERE g.id = %s
                """,
                (group_id,),
            )
            row = await cur.fetchone()
    tariff = str(row[0] if row and row[0] else "free")
    return plan_limit(tariff, "max_team_seats", 1), tariff


def _is_group_admin(role_in_group: Optional[str]) -> bool:
    """Workspace owner (legacy admin/manager aliases included)."""
    return role_in_group in ("owner", "admin", "manager")


def _normalize_role_in_group(role: str) -> str:
    """Map legacy roles to workspace RBAC; accept canonical roles as-is."""
    mapping = {
        "owner": "owner",
        "admin": "owner",
        "manager": "owner",
        "editor": "editor",
        "author": "editor",
        "approver": "approver",
        "viewer": "viewer",
        "analyst": "viewer",
    }
    if role not in mapping:
        raise ValueError(
            "role_in_group must be owner, editor, approver, or viewer"
        )
    return mapping[role]


async def get_membership_in_group(user_id: int, group_id: int) -> Optional[Dict]:
    """Участие пользователя в конкретной группе (для проверки прав)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT g.id, g.name, g.created_at, g.created_by_user_id, gm.role_in_group, gm.joined_at
                FROM group_members gm
                JOIN groups g ON g.id = gm.group_id
                WHERE gm.user_id = %s AND gm.group_id = %s
                """,
                (user_id, group_id),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {
        "group_id": row[0],
        "group_name": row[1],
        "created_at": row[2],
        "created_by_user_id": row[3],
        "role_in_group": row[4],
        "joined_at": row[5],
    }


async def get_user_group_memberships(user_id: int) -> List[Dict]:
    """Все группы пользователя."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT g.id, g.name, gm.role_in_group, gm.joined_at
                FROM group_members gm
                JOIN groups g ON g.id = gm.group_id
                WHERE gm.user_id = %s
                ORDER BY gm.joined_at ASC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
    return [
        {
            "group_id": r[0],
            "group_name": r[1],
            "role_in_group": r[2],
            "joined_at": r[3],
        }
        for r in rows
    ]


async def get_user_group_membership(user_id: int) -> Optional[Dict]:
    """Активная или первая группа пользователя (для профиля)."""
    memberships = await get_user_group_memberships(user_id)
    if not memberships:
        return None
    active_id = await get_user_active_group_id(user_id)
    chosen = memberships[0]
    if active_id is not None:
        for m in memberships:
            if m["group_id"] == active_id:
                chosen = m
                break
    detail = await get_membership_in_group(user_id, chosen["group_id"])
    return detail


async def get_group_member_user_ids(group_id: int) -> List[int]:
    """Список user_id участников группы."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_id FROM group_members WHERE group_id = %s",
                (group_id,),
            )
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def get_group_by_id(group_id: int, include_members: bool = False) -> Optional[Dict]:
    """Группа по id. При include_members — участники с username, email, tariff."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, description, created_at, created_by_user_id
                FROM groups WHERE id = %s
                """,
                (group_id,),
            )
            row = await cur.fetchone()
    if not row:
        return None
    group = {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "created_by_user_id": row[4],
        "members": None,
    }
    if include_members:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT gm.user_id, u.username, u.email, u.tariff, u.role, gm.role_in_group, gm.joined_at
                    FROM group_members gm
                    JOIN users u ON u.id = gm.user_id
                    WHERE gm.group_id = %s
                    ORDER BY gm.role_in_group, gm.joined_at
                    """,
                    (group_id,),
                )
                members_rows = await cur.fetchall()
        group["members"] = [
            {
                "user_id": r[0],
                "username": r[1],
                "email": r[2],
                "tariff": r[3] or "free",
                "role": r[4],
                "role_in_group": r[5],
                "joined_at": r[6],
            }
            for r in members_rows
        ]
    return group


async def get_user_active_group_id(user_id: int) -> Optional[int]:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT active_group_id FROM users WHERE id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None


async def set_active_group(user_id: int, group_id: Optional[int]) -> Optional[int]:
    """Set active workspace; None clears. Must be a member when group_id is set."""
    if group_id is not None:
        membership = await get_membership_in_group(user_id, group_id)
        if not membership:
            raise PermissionError("You are not a member of this workspace")
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE users SET active_group_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING active_group_id
                """,
                (group_id, user_id),
            )
            row = await cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None


async def get_my_group(user_id: int, current_user_role: str) -> Optional[Dict]:
    """
    Workspace for «my» page: active_group_id if set and valid, else first joined.
    Owner sees members; platform admin always sees members.
    """
    memberships = await get_user_group_memberships(user_id)
    if not memberships:
        return None
    active_id = await get_user_active_group_id(user_id)
    chosen = memberships[0]
    if active_id is not None:
        for m in memberships:
            if m["group_id"] == active_id:
                chosen = m
                break
    group_id = chosen["group_id"]
    membership_role = chosen["role_in_group"]
    include_members = _is_group_admin(membership_role) or current_user_role == "admin"
    group = await get_group_by_id(group_id, include_members=include_members)
    if not group:
        return None
    group["role_in_group"] = membership_role
    return group


async def create_group_by_admin(
    name: str, description: Optional[str], created_by_user_id: int
) -> Dict:
    """Создаёт пустую группу (без участников). Только сценарий admin."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO groups (name, description, created_by_user_id)
                VALUES (%s, %s, %s)
                RETURNING id, name, description, created_at, created_by_user_id
                """,
                (name, description or None, created_by_user_id),
            )
            row = await cur.fetchone()
            if not row:
                raise RuntimeError("Failed to create group")
    full = await get_group_by_id(row[0], include_members=True)
    return full if full else {}


async def create_group(user_id: int, name: str, current_user_role: str, description: Optional[str] = None) -> Dict:
    """
    Создаёт workspace и добавляет создателя как owner.
    Роль manager или admin (глобальная); пользователь может состоять и в других группах.
    """
    if current_user_role not in ("manager", "admin"):
        raise PermissionError("Only manager or admin can create a group")

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO groups (name, description, created_by_user_id)
                VALUES (%s, %s, %s)
                RETURNING id, name, description, created_at, created_by_user_id
                """,
                (name, description or None, user_id),
            )
            row = await cur.fetchone()
            if not row:
                raise RuntimeError("Failed to create group")
            group_id = row[0]
            await cur.execute(
                """
                INSERT INTO group_members (group_id, user_id, role_in_group)
                VALUES (%s, %s, 'owner')
                """,
                (group_id, user_id),
            )
            await cur.execute(
                """
                UPDATE users SET active_group_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (group_id, user_id),
            )
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "created_by_user_id": row[4],
        "role_in_group": "owner",
        "members": [],
    }


async def update_group(
    group_id: int,
    requested_by_user_id: int,
    requested_by_role: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict:
    """Обновляет название и/или описание. Менеджер этой группы или admin."""
    if name is None and description is None:
        g = await get_group_by_id(group_id, include_members=False)
        if not g:
            raise ValueError("Group not found")
        return g

    membership = await get_membership_in_group(requested_by_user_id, group_id)
    if requested_by_role != "admin":
        if not membership or not _is_group_admin(membership.get("role_in_group")):
            raise PermissionError("Only group admin or platform admin can update the group")

    updates = []
    params: List = []
    if name is not None:
        updates.append("name = %s")
        params.append(name)
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    params.append(group_id)

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            query = f"UPDATE groups SET {', '.join(updates)} WHERE id = %s RETURNING id, name, description, created_at, created_by_user_id"
            await cur.execute(query, params)
            row = await cur.fetchone()
    if not row:
        raise ValueError("Group not found")
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "created_by_user_id": row[4],
    }


async def add_member_by_email(
    group_id: int,
    email: str,
    requested_by_user_id: int,
    requested_by_role: str,
    role_in_group: str = "editor",
) -> Dict:
    """
    Добавляет участника по email.
    Admin группы или platform admin. Первый участник — только admin.
    В одной группе не может быть двух admin.
    """
    role_in_group = _normalize_role_in_group(role_in_group)

    membership = None
    if requested_by_role != "admin":
        membership = await get_membership_in_group(requested_by_user_id, group_id)
        if not membership or not _is_group_admin(membership.get("role_in_group")):
            raise PermissionError("Only group admin or platform admin can add members")

    n_members = await _count_group_members(group_id)
    if n_members == 0:
        if role_in_group != "owner":
            raise ValueError("The first member of an empty workspace must be an owner")
    else:
        if role_in_group == "owner":
            raise ValueError("Workspace already has an owner; invite as editor, approver, or viewer")
        seat_limit, seat_tariff = await _seat_budget_for_group(group_id)
        if n_members >= seat_limit:
            raise TeamSeatLimitError(limit=seat_limit, used=n_members, tariff=seat_tariff)

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, username, email, tariff FROM users WHERE email = %s", (email,))
            user_row = await cur.fetchone()
            if not user_row:
                raise ValueError("User with this email not found")
            target_user_id = user_row[0]
            await cur.execute(
                "SELECT 1 FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, target_user_id),
            )
            if await cur.fetchone():
                raise ValueError("User is already in this group")
            await cur.execute(
                """
                INSERT INTO group_members (group_id, user_id, role_in_group)
                VALUES (%s, %s, %s)
                """,
                (group_id, target_user_id, role_in_group),
            )
            await cur.execute(
                "SELECT joined_at FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, target_user_id),
            )
            joined_row = await cur.fetchone()
    return {
        "user_id": target_user_id,
        "username": user_row[1],
        "email": user_row[2],
        "tariff": user_row[3] or "free",
        "role_in_group": role_in_group,
        "joined_at": joined_row[0] if joined_row else None,
    }


async def remove_member(
    group_id: int, member_user_id: int, requested_by_user_id: int, requested_by_role: str
) -> None:
    """Удаляет участника. Менеджер группы или admin. Нельзя удалить единственного менеджера."""
    if requested_by_role != "admin":
        membership = await get_membership_in_group(requested_by_user_id, group_id)
        if not membership or not _is_group_admin(membership.get("role_in_group")):
            raise PermissionError("Only group admin or platform admin can remove members")

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT role_in_group FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, member_user_id),
            )
            row = await cur.fetchone()
            if not row:
                raise ValueError("User is not a member of this group")
            if _is_group_admin(row[0]):
                if await _count_managers_in_group(group_id) <= 1:
                    raise ValueError("Cannot remove the only owner of the workspace")
            await cur.execute(
                "DELETE FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, member_user_id),
            )


async def get_all_groups_with_members() -> List[Dict]:
    """Все группы с участниками (admin)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    g.id,
                    g.name,
                    g.description,
                    g.created_at,
                    g.created_by_user_id,
                    gm.user_id,
                    u.username,
                    u.email,
                    u.tariff,
                    u.role,
                    gm.role_in_group,
                    gm.joined_at
                FROM groups g
                LEFT JOIN group_members gm ON gm.group_id = g.id
                LEFT JOIN users u ON u.id = gm.user_id
                ORDER BY g.name, gm.role_in_group, gm.joined_at
                """
            )
            rows = await cur.fetchall()

    groups_by_id: Dict[int, Dict] = {}
    for row in rows:
        group_id = row[0]
        if group_id not in groups_by_id:
            groups_by_id[group_id] = {
                "id": group_id,
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "created_by_user_id": row[4],
                "members": [],
            }
        if row[5] is not None:
            groups_by_id[group_id]["members"].append(
                {
                    "user_id": row[5],
                    "username": row[6],
                    "email": row[7],
                    "tariff": row[8] or "free",
                    "role": row[9],
                    "role_in_group": row[10],
                    "joined_at": row[11],
                }
            )

    return list(groups_by_id.values())


def _invite_row_to_dict(row) -> Dict:
    return {
        "id": row[0],
        "group_id": row[1],
        "email": row[2],
        "role_in_group": row[3],
        "token": row[4],
        "invited_by_user_id": row[5],
        "status": row[6],
        "accepted_by_user_id": row[7],
        "expires_at": row[8],
        "accepted_at": row[9],
        "created_at": row[10],
        "group_name": row[11] if len(row) > 11 else None,
    }


async def _assert_can_manage_invites(
    group_id: int, requested_by_user_id: int, requested_by_role: str
) -> None:
    if requested_by_role == "admin":
        return
    membership = await get_membership_in_group(requested_by_user_id, group_id)
    if not membership or not _is_group_admin(membership.get("role_in_group")):
        raise PermissionError("Only workspace owner can manage invites")


async def create_invite(
    group_id: int,
    requested_by_user_id: int,
    requested_by_role: str,
    *,
    email: Optional[str] = None,
    role_in_group: str = "editor",
    expires_days: int = 7,
) -> Dict:
    """
    Создаёт invite-ссылку.
    Если email уже зарегистрирован и пользователь не в команде — добавляем сразу
    (status=added). Иначе — pending invite с token.
    """
    import secrets
    from datetime import datetime, timedelta, timezone

    role_in_group = _normalize_role_in_group(role_in_group)
    await _assert_can_manage_invites(group_id, requested_by_user_id, requested_by_role)

    group = await get_group_by_id(group_id, include_members=False)
    if not group:
        raise ValueError("Group not found")

    clean_email = (email or "").strip().lower() or None
    if role_in_group == "owner":
        raise ValueError("Workspace already has an owner; use editor, approver, or viewer")

    n_members = await _count_group_members(group_id)
    seat_limit, seat_tariff = await _seat_budget_for_group(group_id)
    if n_members >= seat_limit:
        raise TeamSeatLimitError(limit=seat_limit, used=n_members, tariff=seat_tariff)

    if clean_email:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, username, email, tariff FROM users WHERE lower(email) = %s",
                    (clean_email,),
                )
                user_row = await cur.fetchone()
        if user_row:
            try:
                member = await add_member_by_email(
                    group_id,
                    clean_email,
                    requested_by_user_id,
                    requested_by_role,
                    role_in_group=role_in_group,
                )
                return {
                    "status": "added",
                    "member": member,
                    "invite": None,
                    "group_name": group["name"],
                }
            except ValueError as exc:
                if "already in this group" in str(exc).lower():
                    raise
                # fall through to invite if add failed for other reasons
                pass

    token = secrets.token_urlsafe(32)[:64]
    expires_at = datetime.now(timezone.utc) + timedelta(days=max(1, min(expires_days, 30)))

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO group_invites (
                    group_id, email, role_in_group, token,
                    invited_by_user_id, status, expires_at
                )
                VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                RETURNING id, group_id, email, role_in_group, token,
                          invited_by_user_id, status, accepted_by_user_id,
                          expires_at, accepted_at, created_at
                """,
                (
                    group_id,
                    clean_email,
                    role_in_group,
                    token,
                    requested_by_user_id,
                    expires_at,
                ),
            )
            row = await cur.fetchone()

    invite = _invite_row_to_dict((*row, group["name"]))
    return {
        "status": "invited",
        "member": None,
        "invite": invite,
        "group_name": group["name"],
    }


async def list_pending_invites(
    group_id: int, requested_by_user_id: int, requested_by_role: str
) -> List[Dict]:
    await _assert_can_manage_invites(group_id, requested_by_user_id, requested_by_role)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT i.id, i.group_id, i.email, i.role_in_group, i.token,
                       i.invited_by_user_id, i.status, i.accepted_by_user_id,
                       i.expires_at, i.accepted_at, i.created_at, g.name
                FROM group_invites i
                JOIN groups g ON g.id = i.group_id
                WHERE i.group_id = %s AND i.status = 'pending' AND i.expires_at > NOW()
                ORDER BY i.created_at DESC
                """,
                (group_id,),
            )
            rows = await cur.fetchall()
    return [_invite_row_to_dict(r) for r in rows]


async def revoke_invite(
    group_id: int, invite_id: int, requested_by_user_id: int, requested_by_role: str
) -> None:
    await _assert_can_manage_invites(group_id, requested_by_user_id, requested_by_role)
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE group_invites SET status = 'revoked'
                WHERE id = %s AND group_id = %s AND status = 'pending'
                """,
                (invite_id, group_id),
            )
            if cur.rowcount == 0:
                raise ValueError("Invite not found or already used")


async def get_invite_by_token(token: str) -> Optional[Dict]:
    token = (token or "").strip()
    if not token:
        return None
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT i.id, i.group_id, i.email, i.role_in_group, i.token,
                       i.invited_by_user_id, i.status, i.accepted_by_user_id,
                       i.expires_at, i.accepted_at, i.created_at, g.name
                FROM group_invites i
                JOIN groups g ON g.id = i.group_id
                WHERE i.token = %s
                """,
                (token,),
            )
            row = await cur.fetchone()
    if not row:
        return None
    invite = _invite_row_to_dict(row)
    from datetime import datetime, timezone

    exp = invite.get("expires_at")
    if invite["status"] == "pending" and exp is not None:
        now = datetime.now(timezone.utc)
        exp_aware = exp if getattr(exp, "tzinfo", None) else exp.replace(tzinfo=timezone.utc)
        if exp_aware < now:
            invite["status"] = "expired"
    return invite


async def accept_invite(token: str, user_id: int, user_email: Optional[str] = None) -> Dict:
    """Принимает invite: добавляет пользователя в группу."""
    invite = await get_invite_by_token(token)
    if not invite:
        raise ValueError("Invite not found")
    if invite["status"] != "pending":
        raise ValueError(f"Invite is {invite['status']}")

    group_id = int(invite["group_id"])
    role_in_group = _normalize_role_in_group(invite["role_in_group"])

    if invite.get("email") and user_email:
        if invite["email"].strip().lower() != user_email.strip().lower():
            raise ValueError("This invite was issued for a different email")

    existing = await get_membership_in_group(user_id, group_id)
    if existing:
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE group_invites
                    SET status = 'accepted', accepted_by_user_id = %s, accepted_at = NOW()
                    WHERE id = %s AND status = 'pending'
                    """,
                    (user_id, invite["id"]),
                )
        return {
            "group_id": group_id,
            "group_name": invite.get("group_name"),
            "role_in_group": existing["role_in_group"],
            "already_member": True,
        }

    n_members = await _count_group_members(group_id)
    seat_limit, seat_tariff = await _seat_budget_for_group(group_id)
    if n_members >= seat_limit:
        raise TeamSeatLimitError(limit=seat_limit, used=n_members, tariff=seat_tariff)
    if role_in_group == "owner":
        raise ValueError("Workspace already has an owner; use editor, approver, or viewer")

    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO group_members (group_id, user_id, role_in_group)
                VALUES (%s, %s, %s)
                ON CONFLICT (group_id, user_id) DO NOTHING
                """,
                (group_id, user_id, role_in_group),
            )
            await cur.execute(
                """
                UPDATE group_invites
                SET status = 'accepted', accepted_by_user_id = %s, accepted_at = NOW()
                WHERE id = %s AND status = 'pending'
                """,
                (user_id, invite["id"]),
            )

    return {
        "group_id": group_id,
        "group_name": invite.get("group_name"),
        "role_in_group": role_in_group,
        "already_member": False,
    }
