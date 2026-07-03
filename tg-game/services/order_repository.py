"""Заказы из режима menu."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional

from database import (
    commit_connection,
    get_db_connection,
    release_db_connection,
    rollback_connection,
)
from services.cart_repository import cart_repository


class OrderRepository:
    async def checkout(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
        username: Optional[str],
        first_name: Optional[str],
    ) -> Optional[dict[str, Any]]:
        items = await cart_repository.list_items(
            bot_id=bot_id,
            telegram_user_id=telegram_user_id,
            mode_id=mode_id,
        )
        if not items:
            return None

        total_amount = sum((item.line_total for item in items), Decimal("0"))

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                placeholder = f"P-{uuid.uuid4().hex}"
                await cur.execute(
                    """
                    INSERT INTO game_menu_orders
                    (bot_id, mode_id, telegram_user_id, username, first_name,
                     order_number, status, total_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, 'placed', %s)
                    RETURNING id
                    """,
                    (
                        bot_id,
                        mode_id,
                        telegram_user_id,
                        username,
                        first_name,
                        placeholder,
                        total_amount,
                    ),
                )
                order_row = await cur.fetchone()
                order_id = int(order_row[0])
                order_number = f"ORD-{mode_id}-{order_id:06d}"

                await cur.execute(
                    "UPDATE game_menu_orders SET order_number = %s WHERE id = %s",
                    (order_number, order_id),
                )

                for item in items:
                    await cur.execute(
                        """
                        INSERT INTO game_menu_order_items
                        (order_id, node_id, title, quantity, unit_price)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (order_id, item.node_id, item.title, item.quantity, item.unit_price),
                    )

                await cur.execute(
                    """
                    DELETE FROM game_menu_cart_items
                    WHERE cart_id IN (
                        SELECT id FROM game_menu_carts
                        WHERE bot_id = %s AND telegram_user_id = %s AND mode_id = %s
                    )
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )

                await commit_connection(conn)
                return {
                    "id": order_id,
                    "order_number": order_number,
                    "total_amount": float(total_amount),
                    "items": [
                        {
                            "node_id": i.node_id,
                            "title": i.title,
                            "quantity": i.quantity,
                            "unit_price": float(i.unit_price),
                            "line_total": float(i.line_total),
                        }
                        for i in items
                    ],
                }
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def admin_list_orders(
        self,
        *,
        mode_id: Optional[int] = None,
        bot_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                conditions: list[str] = []
                vals: list[Any] = []
                if mode_id is not None:
                    conditions.append("o.mode_id = %s")
                    vals.append(mode_id)
                if bot_id is not None:
                    conditions.append("o.bot_id = %s")
                    vals.append(bot_id)
                where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                vals.append(limit)
                await cur.execute(
                    f"""
                    SELECT o.id, o.order_number, o.bot_id, o.mode_id, m.title,
                           o.telegram_user_id, o.username, o.first_name,
                           o.status, o.created_at, o.total_amount,
                           COALESCE((
                               SELECT SUM(oi.quantity) FROM game_menu_order_items oi
                               WHERE oi.order_id = o.id
                           ), 0) AS total_qty
                    FROM game_menu_orders o
                    JOIN game_modes m ON m.id = o.mode_id
                    {where_sql}
                    ORDER BY o.created_at DESC
                    LIMIT %s
                    """,
                    vals,
                )
                rows = await cur.fetchall()
                result = [
                    {
                        "id": int(r[0]),
                        "order_number": str(r[1]),
                        "bot_id": int(r[2]),
                        "mode_id": int(r[3]),
                        "mode_title": str(r[4]),
                        "telegram_user_id": int(r[5]),
                        "username": r[6],
                        "first_name": r[7],
                        "status": str(r[8]),
                        "created_at": r[9].isoformat() if r[9] else None,
                        "total_amount": float(r[10]) if r[10] is not None else 0.0,
                        "total_quantity": int(r[11]),
                    }
                    for r in rows
                ]
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)

    async def admin_get_order(self, order_id: int) -> Optional[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT o.id, o.order_number, o.bot_id, o.mode_id, m.title,
                           o.telegram_user_id, o.username, o.first_name,
                           o.status, o.created_at, o.total_amount
                    FROM game_menu_orders o
                    JOIN game_modes m ON m.id = o.mode_id
                    WHERE o.id = %s
                    """,
                    (order_id,),
                )
                row = await cur.fetchone()
                if not row:
                    await commit_connection(conn)
                    return None

                await cur.execute(
                    """
                    SELECT id, node_id, title, quantity, unit_price
                    FROM game_menu_order_items
                    WHERE order_id = %s
                    ORDER BY id
                    """,
                    (order_id,),
                )
                item_rows = await cur.fetchall()
                result = {
                    "id": int(row[0]),
                    "order_number": str(row[1]),
                    "bot_id": int(row[2]),
                    "mode_id": int(row[3]),
                    "mode_title": str(row[4]),
                    "telegram_user_id": int(row[5]),
                    "username": row[6],
                    "first_name": row[7],
                    "status": str(row[8]),
                    "created_at": row[9].isoformat() if row[9] else None,
                    "total_amount": float(row[10]) if row[10] is not None else 0.0,
                    "items": [
                        {
                            "id": int(ir[0]),
                            "node_id": int(ir[1]) if ir[1] is not None else None,
                            "title": str(ir[2]),
                            "quantity": int(ir[3]),
                            "unit_price": float(ir[4]) if ir[4] is not None else 0.0,
                            "line_total": float(Decimal(str(ir[4])) * int(ir[3]))
                            if ir[4] is not None
                            else 0.0,
                        }
                        for ir in item_rows
                    ],
                }
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)


order_repository = OrderRepository()
