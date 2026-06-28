"""Доступ к узлам иерархического меню."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from database import (
    commit_connection,
    get_db_connection,
    release_db_connection,
    rollback_connection,
)
from services.media_storage import resolve_public_media_url

_NODE_SELECT = """
    id, mode_id, parent_id, title, body_text, image_url,
    image_file_id, sort_order, is_active, price
"""


@dataclass(slots=True)
class GameMenuNodeRow:
    id: int
    mode_id: int
    parent_id: Optional[int]
    title: str
    body_text: Optional[str]
    image_url: Optional[str]
    image_file_id: Optional[str]
    sort_order: int
    is_active: bool
    price: Decimal = Decimal("0")


@dataclass(slots=True)
class GameMenuNodeView:
    node: GameMenuNodeRow
    has_children: bool


class MenuRepository:
    async def list_children(
        self,
        mode_id: int,
        parent_id: Optional[int],
        *,
        active_only: bool = True,
    ) -> list[GameMenuNodeRow]:
        views = await self.list_children_views(mode_id, parent_id, active_only=active_only)
        return [v.node for v in views]

    async def list_children_views(
        self,
        mode_id: int,
        parent_id: Optional[int],
        *,
        active_only: bool = True,
    ) -> list[GameMenuNodeView]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if parent_id is None:
                    sql = f"""
                        SELECT {_NODE_SELECT},
                               EXISTS(
                                   SELECT 1 FROM game_menu_nodes ch
                                   WHERE ch.parent_id = game_menu_nodes.id
                               ) AS has_children
                        FROM game_menu_nodes
                        WHERE mode_id = %s AND parent_id IS NULL
                    """
                    params: list[Any] = [mode_id]
                else:
                    sql = f"""
                        SELECT {_NODE_SELECT},
                               EXISTS(
                                   SELECT 1 FROM game_menu_nodes ch
                                   WHERE ch.parent_id = game_menu_nodes.id
                               ) AS has_children
                        FROM game_menu_nodes
                        WHERE mode_id = %s AND parent_id = %s
                    """
                    params = [mode_id, parent_id]
                if active_only:
                    sql += " AND is_active = TRUE"
                sql += " ORDER BY sort_order, id"
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                result = [
                    GameMenuNodeView(
                        node=self._row_to_node(r[:10]),
                        has_children=bool(r[10]),
                    )
                    for r in rows
                ]
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)

    async def get_node(self, node_id: int) -> Optional[GameMenuNodeRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {_NODE_SELECT} FROM game_menu_nodes WHERE id = %s",
                    (node_id,),
                )
                row = await cur.fetchone()
                if not row:
                    await commit_connection(conn)
                    return None
                result = self._row_to_node(row)
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)

    async def has_children(self, node_id: int, *, active_only: bool = True) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                sql = "SELECT 1 FROM game_menu_nodes WHERE parent_id = %s"
                if active_only:
                    sql += " AND is_active = TRUE"
                sql += " LIMIT 1"
                await cur.execute(sql, (node_id,))
                found = await cur.fetchone() is not None
                await commit_connection(conn)
                return found
        finally:
            await release_db_connection(conn)

    async def is_orderable_leaf(self, node_id: int) -> bool:
        """True только для конечной позиции без вложенных подпунктов."""
        return not await self.has_children(node_id, active_only=False)

    async def find_node_id_by_parent_and_title(
        self,
        mode_id: int,
        parent_id: Optional[int],
        title: str,
    ) -> Optional[int]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if parent_id is None:
                    await cur.execute(
                        """
                        SELECT id FROM game_menu_nodes
                        WHERE mode_id = %s AND parent_id IS NULL AND title = %s
                        LIMIT 1
                        """,
                        (mode_id, title),
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id FROM game_menu_nodes
                        WHERE mode_id = %s AND parent_id = %s AND title = %s
                        LIMIT 1
                        """,
                        (mode_id, parent_id, title),
                    )
                row = await cur.fetchone()
                out = int(row[0]) if row else None
                await commit_connection(conn)
                return out
        finally:
            await release_db_connection(conn)

    async def admin_list_nodes(self, mode_id: int) -> list[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT {_NODE_SELECT}
                    FROM game_menu_nodes
                    WHERE mode_id = %s
                    ORDER BY COALESCE(parent_id, 0), sort_order, id
                    """,
                    (mode_id,),
                )
                rows = await cur.fetchall()
                result = [
                    {
                        "id": int(r[0]),
                        "mode_id": int(r[1]),
                        "parent_id": int(r[2]) if r[2] is not None else None,
                        "title": str(r[3]),
                        "body_text": r[4],
                        "image_url": resolve_public_media_url(r[5]),
                        "image_file_id": r[6],
                        "sort_order": int(r[7]),
                        "is_active": bool(r[8]),
                        "price": float(r[9]) if r[9] is not None else 0.0,
                    }
                    for r in rows
                ]
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)

    async def admin_create_node(
        self,
        *,
        mode_id: int,
        parent_id: Optional[int],
        title: str,
        body_text: Optional[str],
        image_url: Optional[str],
        sort_order: int = 0,
        is_active: bool = True,
        price: Decimal | float = 0,
    ) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_menu_nodes
                    (mode_id, parent_id, title, body_text, image_url, sort_order, is_active, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (mode_id, parent_id, title, body_text, image_url, sort_order, is_active, price),
                )
                row = await cur.fetchone()
                await commit_connection(conn)
                return int(row[0])
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def admin_update_node(
        self,
        node_id: int,
        *,
        parent_id: Optional[int] = None,
        parent_id_set: bool = False,
        title: Optional[str] = None,
        body_text: Optional[str] = None,
        image_url: Optional[str] = None,
        image_url_set: bool = False,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None,
        price: Optional[Decimal | float] = None,
    ) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                fields: list[str] = []
                vals: list[Any] = []
                if parent_id_set:
                    fields.append("parent_id = %s")
                    vals.append(parent_id)
                if title is not None:
                    fields.append("title = %s")
                    vals.append(title)
                if body_text is not None:
                    fields.append("body_text = %s")
                    vals.append(body_text)
                if image_url_set:
                    fields.append("image_url = %s")
                    vals.append(image_url)
                if sort_order is not None:
                    fields.append("sort_order = %s")
                    vals.append(sort_order)
                if is_active is not None:
                    fields.append("is_active = %s")
                    vals.append(is_active)
                if price is not None:
                    fields.append("price = %s")
                    vals.append(price)
                if not fields:
                    await commit_connection(conn)
                    return True
                vals.append(node_id)
                await cur.execute(
                    f"UPDATE game_menu_nodes SET {', '.join(fields)} WHERE id = %s",
                    vals,
                )
                await commit_connection(conn)
                return True
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def admin_delete_node(self, node_id: int) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM game_menu_nodes WHERE id = %s", (node_id,))
                deleted = cur.rowcount > 0
                await commit_connection(conn)
                return deleted
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def set_node_image_file_id(self, node_id: int, image_file_id: str) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE game_menu_nodes SET image_file_id = %s WHERE id = %s",
                    (image_file_id, node_id),
                )
                await commit_connection(conn)
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    def _row_to_node(self, r: tuple) -> GameMenuNodeRow:
        return GameMenuNodeRow(
            id=int(r[0]),
            mode_id=int(r[1]),
            parent_id=int(r[2]) if r[2] is not None else None,
            title=str(r[3]),
            body_text=r[4],
            image_url=r[5],
            image_file_id=r[6],
            sort_order=int(r[7]),
            is_active=bool(r[8]),
            price=Decimal(str(r[9])) if len(r) > 9 and r[9] is not None else Decimal("0"),
        )


menu_repository = MenuRepository()
