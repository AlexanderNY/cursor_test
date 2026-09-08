"""Workspace (group) membership helpers for shared brands and RBAC."""

from __future__ import annotations

from typing import Any, Optional

from database import get_db_connection, release_db_connection

# Canonical workspace roles. Legacy aliases accepted on read/write normalize.
CANONICAL_ROLES = ("owner", "editor", "approver", "viewer")

_ROLE_ALIASES = {
    "owner": "owner",
    "admin": "owner",
    "manager": "owner",
    "editor": "editor",
    "author": "editor",
    "approver": "approver",
    "viewer": "viewer",
    "analyst": "viewer",
}


def normalize_role(role: Optional[str]) -> Optional[str]:
    if role is None:
        return None
    return _ROLE_ALIASES.get(role)


def is_owner_role(role: Optional[str]) -> bool:
    return normalize_role(role) == "owner"


def is_admin_role(role: Optional[str]) -> bool:
    """Legacy alias: workspace owner."""
    return is_owner_role(role)


def can_view_role(role: Optional[str]) -> bool:
    """Any workspace member (or solo user) may view shared content."""
    if role is None:
        return True
    return normalize_role(role) in CANONICAL_ROLES


def can_edit_role(role: Optional[str]) -> bool:
    """Owner/Editor may create and edit drafts; solo users may edit."""
    if role is None:
        return True
    return normalize_role(role) in ("owner", "editor")


def can_publish_role(role: Optional[str]) -> bool:
    """Same as edit: Viewer/Approver cannot create or mutate jobs."""
    return can_edit_role(role)


def can_approve_role(role: Optional[str]) -> bool:
    """Owner/Approver may approve/reject; solo users may approve."""
    if role is None:
        return True
    return normalize_role(role) in ("owner", "approver")


def can_manage_members_role(role: Optional[str]) -> bool:
    return is_owner_role(role)


async def list_memberships(user_id: int) -> list[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT group_id, role_in_group
                FROM group_members
                WHERE user_id = %s
                ORDER BY joined_at ASC
                """,
                (user_id,),
            )
            rows = await cur.fetchall()
    finally:
        await release_db_connection(conn)
    return [{"group_id": int(r[0]), "role_in_group": r[1]} for r in rows]


async def group_ids_for_user(user_id: int) -> list[int]:
    return [m["group_id"] for m in await list_memberships(user_id)]


async def role_in_group(user_id: int, group_id: int) -> Optional[str]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT role_in_group FROM group_members
                WHERE user_id = %s AND group_id = %s
                """,
                (user_id, group_id),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    return row[0] if row else None


async def get_active_group_id(user_id: int) -> Optional[int]:
    """Prefer users.active_group_id when still a member; else first membership."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT active_group_id FROM users WHERE id = %s",
                (user_id,),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    active = int(row[0]) if row and row[0] is not None else None
    memberships = await list_memberships(user_id)
    if not memberships:
        return None
    if active is not None and any(m["group_id"] == active for m in memberships):
        return active
    return int(memberships[0]["group_id"])


async def primary_membership(user_id: int) -> Optional[dict[str, Any]]:
    active = await get_active_group_id(user_id)
    memberships = await list_memberships(user_id)
    if not memberships:
        return None
    if active is not None:
        for m in memberships:
            if m["group_id"] == active:
                return m
    return memberships[0]


async def is_team_admin(user_id: int, group_id: Optional[int] = None) -> bool:
    if group_id is not None:
        return is_owner_role(await role_in_group(user_id, group_id))
    return any(is_owner_role(m["role_in_group"]) for m in await list_memberships(user_id))


async def can_manage_platform_auth(user_id: int) -> bool:
    """Auth tabs / credential writes: solo user or workspace owner."""
    memberships = await list_memberships(user_id)
    if not memberships:
        return True
    return any(is_owner_role(m["role_in_group"]) for m in memberships)


async def can_view_team_stats(user_id: int) -> bool:
    """Analytics for shared workspace data: any member (incl. Viewer)."""
    memberships = await list_memberships(user_id)
    if not memberships:
        return True
    return any(can_view_role(m["role_in_group"]) for m in memberships)


async def brand_role_for_user(user_id: int, brand: dict[str, Any]) -> Optional[str]:
    if int(brand.get("user_id") or 0) == int(user_id):
        return "owner"
    gid = brand.get("group_id")
    if gid is None:
        return None
    return await role_in_group(user_id, int(gid))


async def can_access_brand_row(user_id: int, brand: dict[str, Any]) -> bool:
    role = await brand_role_for_user(user_id, brand)
    if int(brand.get("user_id") or 0) == int(user_id):
        return True
    return can_view_role(role) if role else False


async def can_manage_brand(user_id: int, brand: dict[str, Any]) -> bool:
    """Create/update/delete brand & channels / bind auth: brand owner or workspace owner."""
    if int(brand.get("user_id") or 0) == int(user_id):
        return True
    gid = brand.get("group_id")
    if gid is None:
        return False
    return is_owner_role(await role_in_group(user_id, int(gid)))


async def can_edit_brand_content(user_id: int, brand: dict[str, Any]) -> bool:
    if int(brand.get("user_id") or 0) == int(user_id):
        return True
    role = await brand_role_for_user(user_id, brand)
    return can_edit_role(role)


async def can_approve_brand_content(user_id: int, brand: dict[str, Any]) -> bool:
    if int(brand.get("user_id") or 0) == int(user_id) and brand.get("group_id") is None:
        return True
    role = await brand_role_for_user(user_id, brand)
    return can_approve_role(role)


async def default_admin_group_id(user_id: int) -> Optional[int]:
    """First group where the user is owner — used to auto-link new brands."""
    for m in await list_memberships(user_id):
        if is_owner_role(m["role_in_group"]):
            return int(m["group_id"])
    return None


async def brand_credential_user_id(brand: dict[str, Any]) -> int:
    """Platform tokens always belong to the brand owner."""
    return int(brand["user_id"])


async def brand_access_clause(
    user_id: int,
    *,
    brand_alias: Optional[str] = "b",
) -> tuple[str, list[Any]]:
    """SQL fragment: user owns brand OR is member of brand.group_id."""
    gids = await group_ids_for_user(user_id)
    if brand_alias:
        col_user = f"{brand_alias}.user_id"
        col_group = f"{brand_alias}.group_id"
    else:
        col_user = "user_id"
        col_group = "group_id"
    if gids:
        return f"({col_user} = %s OR {col_group} = ANY(%s))", [user_id, gids]
    return f"{col_user} = %s", [user_id]


async def shared_brand_ids(user_id: int) -> list[int]:
    """Brand ids visible to user (owned + team-shared)."""
    clause, params = await brand_access_clause(user_id, brand_alias=None)
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"SELECT id FROM smm_brands WHERE {clause}",
                params,
            )
            rows = await cur.fetchall()
    finally:
        await release_db_connection(conn)
    return [int(r[0]) for r in rows]
