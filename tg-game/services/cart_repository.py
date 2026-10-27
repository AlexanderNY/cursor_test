"""Корзина заказов для режима menu."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from database import (
    commit_connection,
    get_db_connection,
    release_db_connection,
    rollback_connection,
)
from services.order_desk import is_payment_method, next_quantity


@dataclass(slots=True)
class CartItemRow:
    node_id: int
    title: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


class CartRepository:
    async def _get_or_create_cart_id(
        self,
        cur,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
    ) -> int:
        await cur.execute(
            """
            INSERT INTO game_menu_carts (bot_id, telegram_user_id, mode_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (bot_id, telegram_user_id, mode_id) DO UPDATE
                SET updated_at = NOW()
            RETURNING id
            """,
            (bot_id, telegram_user_id, mode_id),
        )
        row = await cur.fetchone()
        return int(row[0])

    async def add_item(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
        node_id: int,
    ) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 1 FROM game_menu_nodes
                    WHERE parent_id = %s
                    LIMIT 1
                    """,
                    (node_id,),
                )
                if await cur.fetchone() is not None:
                    raise ValueError("Раздел с подпунктами нельзя добавить в заказ")

                cart_id = await self._get_or_create_cart_id(
                    cur,
                    bot_id=bot_id,
                    telegram_user_id=telegram_user_id,
                    mode_id=mode_id,
                )
                await cur.execute(
                    """
                    INSERT INTO game_menu_cart_items (cart_id, node_id, quantity)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (cart_id, node_id) DO UPDATE
                        SET quantity = game_menu_cart_items.quantity + 1
                    """,
                    (cart_id, node_id),
                )
                total = await self._count_items(cur, cart_id)
                await commit_connection(conn)
                return total
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def clear_cart(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
    ) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
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
                await cur.execute(
                    """
                    UPDATE game_menu_carts
                    SET payment_method = NULL, updated_at = NOW()
                    WHERE bot_id = %s AND telegram_user_id = %s AND mode_id = %s
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )
                await commit_connection(conn)
                return True
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def get_cart_total(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
    ) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id FROM game_menu_carts c
                    WHERE c.bot_id = %s AND c.telegram_user_id = %s AND c.mode_id = %s
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )
                row = await cur.fetchone()
                if not row:
                    await commit_connection(conn)
                    return 0
                total = await self._count_items(cur, int(row[0]))
                await commit_connection(conn)
                return total
        finally:
            await release_db_connection(conn)

    async def change_quantity(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
        node_id: int,
        delta: int,
    ) -> int:
        """Меняет количество позиции. 0 — строка удалена или её не было."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id FROM game_menu_carts
                    WHERE bot_id = %s AND telegram_user_id = %s AND mode_id = %s
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )
                cart_row = await cur.fetchone()
                if not cart_row:
                    await commit_connection(conn)
                    return 0
                cart_id = int(cart_row[0])
                await cur.execute(
                    """
                    SELECT quantity FROM game_menu_cart_items
                    WHERE cart_id = %s AND node_id = %s
                    """,
                    (cart_id, node_id),
                )
                item_row = await cur.fetchone()
                if not item_row:
                    await commit_connection(conn)
                    return 0
                updated = next_quantity(int(item_row[0]), delta)
                if updated <= 0:
                    await cur.execute(
                        """
                        DELETE FROM game_menu_cart_items
                        WHERE cart_id = %s AND node_id = %s
                        """,
                        (cart_id, node_id),
                    )
                else:
                    await cur.execute(
                        """
                        UPDATE game_menu_cart_items
                        SET quantity = %s
                        WHERE cart_id = %s AND node_id = %s
                        """,
                        (updated, cart_id, node_id),
                    )
                await commit_connection(conn)
                return updated
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def remove_item(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
        node_id: int,
    ) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM game_menu_cart_items
                    WHERE node_id = %s
                      AND cart_id IN (
                          SELECT id FROM game_menu_carts
                          WHERE bot_id = %s AND telegram_user_id = %s AND mode_id = %s
                      )
                    """,
                    (node_id, bot_id, telegram_user_id, mode_id),
                )
                await commit_connection(conn)
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def get_payment_method(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
    ) -> str | None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT payment_method FROM game_menu_carts
                    WHERE bot_id = %s AND telegram_user_id = %s AND mode_id = %s
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )
                row = await cur.fetchone()
                await commit_connection(conn)
                if not row or not row[0]:
                    return None
                return str(row[0])
        finally:
            await release_db_connection(conn)

    async def set_payment_method(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
        payment_method: str,
    ) -> str:
        if not is_payment_method(payment_method):
            raise ValueError("Неизвестный способ оплаты")
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                cart_id = await self._get_or_create_cart_id(
                    cur,
                    bot_id=bot_id,
                    telegram_user_id=telegram_user_id,
                    mode_id=mode_id,
                )
                await cur.execute(
                    """
                    UPDATE game_menu_carts
                    SET payment_method = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (payment_method, cart_id),
                )
                await commit_connection(conn)
                return payment_method
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)

    async def list_items(
        self,
        *,
        bot_id: int,
        telegram_user_id: int,
        mode_id: int,
    ) -> list[CartItemRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT ci.node_id, n.title, ci.quantity, n.price
                    FROM game_menu_cart_items ci
                    JOIN game_menu_carts c ON c.id = ci.cart_id
                    JOIN game_menu_nodes n ON n.id = ci.node_id
                    WHERE c.bot_id = %s AND c.telegram_user_id = %s AND c.mode_id = %s
                    ORDER BY ci.id
                    """,
                    (bot_id, telegram_user_id, mode_id),
                )
                rows = await cur.fetchall()
                result = [
                    CartItemRow(
                        node_id=int(r[0]),
                        title=str(r[1]),
                        quantity=int(r[2]),
                        unit_price=Decimal(str(r[3])) if r[3] is not None else Decimal("0"),
                    )
                    for r in rows
                ]
                await commit_connection(conn)
                return result
        finally:
            await release_db_connection(conn)

    async def _count_items(self, cur, cart_id: int) -> int:
        await cur.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM game_menu_cart_items WHERE cart_id = %s",
            (cart_id,),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


cart_repository = CartRepository()
