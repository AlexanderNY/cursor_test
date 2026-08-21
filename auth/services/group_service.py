"""Сервис для работы с рабочими группами (пользователь может состоять в нескольких группах)."""

from typing import Dict, List, Optional

from database import get_db_connection


async def _count_group_members(group_id: int) -> int:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM group_members WHERE group_id = %s",
                (group_id,),
            )
            row = await cur.fetchone()
    return int(row[0]) if row else 0


async def _count_managers_in_group(group_id: int) -> int:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM group_members
                WHERE group_id = %s AND role_in_group = 'admin'
                """,
                (group_id,),
            )
            row = await cur.fetchone()
    return int(row[0]) if row else 0


def _is_group_admin(role_in_group: Optional[str]) -> bool:
    return role_in_group == "admin"


def _normalize_role_in_group(role: str) -> str:
    """Map legacy roles to SMM RBAC; accept new roles as-is."""
    mapping = {
        "manager": "admin",
        "author": "editor",
        "admin": "admin",
        "editor": "editor",
        "analyst": "analyst",
    }
    if role not in mapping:
        raise ValueError("role_in_group must be admin, editor, or analyst")
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
    """Первая группа по дате вступления (совместимость с профилем, полный список — get_user_group_memberships)."""
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT g.id, g.name, g.created_at, g.created_by_user_id, gm.role_in_group, gm.joined_at
                FROM group_members gm
                JOIN groups g ON g.id = gm.group_id
                WHERE gm.user_id = %s
                ORDER BY gm.joined_at ASC
                LIMIT 1
                """,
                (user_id,),
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


async def get_my_group(user_id: int, current_user_role: str) -> Optional[Dict]:
    """
    Группа для «моей» страницы: первая по дате вступления.
    Для менеджера этой группы — с участниками (если manager в этой группе); admin — всегда с участниками.
    """
    memberships = await get_user_group_memberships(user_id)
    if not memberships:
        return None
    group_id = memberships[0]["group_id"]
    membership_role = memberships[0]["role_in_group"]
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
    Создаёт группу и добавляет создателя как admin (SMM RBAC).
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
                VALUES (%s, %s, 'admin')
                """,
                (group_id, user_id),
            )
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "created_by_user_id": row[4],
        "role_in_group": "admin",
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
        if role_in_group != "admin":
            raise ValueError("The first member of an empty group must be an admin")
    else:
        if role_in_group == "admin" and await _count_managers_in_group(group_id) >= 1:
            raise ValueError("This group already has an admin")

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
                    raise ValueError("Cannot remove the only admin of the group")
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
