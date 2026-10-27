"""Создаёт режим «Стол заказов» и каталог, если у бота его ещё нет."""

from __future__ import annotations

from database import (
    commit_connection,
    get_db_connection,
    release_db_connection,
    rollback_connection,
)
from services.order_desk import ORDER_DESK_CODE, ORDER_DESK_TITLE, order_desk_categories


async def ensure_order_desk(bot_id: int) -> None:
    """Режим меню и три категории по десять товаров. Повторный запуск каталог не затирает."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO game_modes (
                    bot_id, code, title, is_active, questions_per_game, mode_type
                )
                SELECT %s, %s, %s, TRUE, 1, 'menu'
                WHERE NOT EXISTS (
                    SELECT 1 FROM game_modes
                    WHERE bot_id = %s AND code = %s
                )
                """,
                (bot_id, ORDER_DESK_CODE, ORDER_DESK_TITLE, bot_id, ORDER_DESK_CODE),
            )
            await cur.execute(
                """
                SELECT id FROM game_modes
                WHERE bot_id = %s AND code = %s
                """,
                (bot_id, ORDER_DESK_CODE),
            )
            mode_row = await cur.fetchone()
            if not mode_row:
                await commit_connection(conn)
                return
            mode_id = int(mode_row[0])
            await cur.execute(
                "SELECT COUNT(*) FROM game_menu_nodes WHERE mode_id = %s",
                (mode_id,),
            )
            count_row = await cur.fetchone()
            if count_row and int(count_row[0]) > 0:
                await commit_connection(conn)
                return

            for category_order, category in enumerate(order_desk_categories(), start=1):
                await cur.execute(
                    """
                    INSERT INTO game_menu_nodes
                    (mode_id, parent_id, title, body_text, sort_order, is_active, price)
                    VALUES (%s, NULL, %s, %s, %s, TRUE, 0)
                    RETURNING id
                    """,
                    (mode_id, category.title, category.description, category_order),
                )
                parent_row = await cur.fetchone()
                parent_id = int(parent_row[0])
                for product_order, product in enumerate(category.products, start=1):
                    await cur.execute(
                        """
                        INSERT INTO game_menu_nodes
                        (mode_id, parent_id, title, body_text, sort_order, is_active, price)
                        VALUES (%s, %s, %s, %s, %s, TRUE, %s)
                        """,
                        (
                            mode_id,
                            parent_id,
                            product.title,
                            product.description,
                            product_order,
                            product.price_rub,
                        ),
                    )
            await commit_connection(conn)
    except Exception:
        await rollback_connection(conn)
        raise
    finally:
        await release_db_connection(conn)
