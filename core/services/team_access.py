"""Team (group) membership helpers for shared brands and RBAC."""

from __future__ import annotations

from typing import Any, Optional

from database import get_db_connection, release_db_connection


def is_admin_role(role: Optional[str]) -> bool:
    return role in ("admin", "manager")


def can_publish_role(role: Optional[str]) -> bool:
    """Any team member may post; solo users (no role) may post."""
    if role is None:
        return True
    return role in ("admin", "manager", "editor", "author", "analyst")


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


async def primary_membership(user_id: int) -> Optional[dict[str, Any]]:
    memberships = await list_memberships(user_id)
    return memberships[0] if memberships else None


async def is_team_admin(user_id: int, group_id: Optional[int] = None) -> bool:
    if group_id is not None:
        return is_admin_role(await role_in_group(user_id, group_id))
    return any(is_admin_role(m["role_in_group"]) for m in await list_memberships(user_id))


async def can_manage_platform_auth(user_id: int) -> bool:
    """Auth tabs / credential writes: solo user or team admin."""
    memberships = await list_memberships(user_id)
    if not memberships:
        return True
    return any(is_admin_role(m["role_in_group"]) for m in memberships)


async def can_view_team_stats(user_id: int) -> bool:
    """Statistics / analytics for shared team data: solo or team admin."""
    return await can_manage_platform_auth(user_id)


async def can_access_brand_row(user_id: int, brand: dict[str, Any]) -> bool:
    if int(brand.get("user_id") or 0) == int(user_id):
        return True
    gid = brand.get("group_id")
    if gid is None:
        return False
    role = await role_in_group(user_id, int(gid))
    return can_publish_role(role)


async def can_manage_brand(user_id: int, brand: dict[str, Any]) -> bool:
    """Create/update/delete brand & channels / bind auth: owner or team admin."""
    if int(brand.get("user_id") or 0) == int(user_id):
        return True
    gid = brand.get("group_id")
    if gid is None:
        return False
    return is_admin_role(await role_in_group(user_id, int(gid)))


async def default_admin_group_id(user_id: int) -> Optional[int]:
    """First group where the user is admin — used to auto-link new brands."""
    for m in await list_memberships(user_id):
        if is_admin_role(m["role_in_group"]):
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