"""Адрес доставки игрока в столе заказов."""

from __future__ import annotations

from database import (
    commit_connection,
    get_db_connection,
    release_db_connection,
    rollback_connection,
)


class ProfileRepository:
    async def get_address(self, *, bot_id: int, telegram_user_id: int) -> str:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT delivery_address
                    FROM game_player_profiles
                    WHERE bot_id = %s AND telegram_user_id = %s
                    """,
                    (bot_id, telegram_user_id),
                )
                row = await cur.fetchone()
                await commit_connection(conn)
                if not row or row[0] is None:
                    return ""
                return str(row[0]).strip()
        finally:
            await release_db_connection(conn)

    async def set_address(self, *, bot_id: int, telegram_user_id: int, address: str) -> str:
        cleaned = address.strip()
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_player_profiles (bot_id, telegram_user_id, delivery_address)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (bot_id, telegram_user_id) DO UPDATE SET
                        delivery_address = EXCLUDED.delivery_address,
                        updated_at = NOW()
                    RETURNING delivery_address
                    """,
                    (bot_id, telegram_user_id, cleaned),
                )
                row = await cur.fetchone()
                await commit_connection(conn)
                return str(row[0])
        except Exception:
            await rollback_connection(conn)
            raise
        finally:
            await release_db_connection(conn)


profile_repository = ProfileRepository()
