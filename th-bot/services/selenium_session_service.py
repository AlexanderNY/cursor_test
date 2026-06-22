"""Запись статусов диагностических сессий Selenium (threads_selenium_sessions)."""

import logging
from typing import Any, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


async def insert_session_running(user_id: int) -> int:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO threads_selenium_sessions (user_id, status, detail_message)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, "running", None),
            )
            row = await cur.fetchone()
            return int(row[0])
    finally:
        release_db_connection(conn)


async def update_session(session_id: int, status: str, detail_message: Optional[str]) -> None:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE threads_selenium_sessions
                SET status = %s, detail_message = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (status, (detail_message or "")[:4000], session_id),
            )
    finally:
        release_db_connection(conn)


async def get_last_session(user_id: int) -> Optional[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, status, detail_message, created_at, updated_at
                FROM threads_selenium_sessions
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            desc = [c.name for c in cur.description]
            out = dict(zip(desc, row))
            if out.get("created_at") is not None:
                out["created_at"] = out["created_at"].isoformat()
            if out.get("updated_at") is not None:
                out["updated_at"] = out["updated_at"].isoformat()
            return out
    finally:
        release_db_connection(conn)


async def get_session_by_id(session_id: int, user_id: int) -> Optional[dict[str, Any]]:
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, status, detail_message, created_at, updated_at
                FROM threads_selenium_sessions
                WHERE id = %s AND user_id = %s
                """,
                (session_id, user_id),
            )
            row = await cur.fetchone()
            if not row:
                return None
            desc = [c.name for c in cur.description]
            out = dict(zip(desc, row))
            if out.get("created_at") is not None:
                out["created_at"] = out["created_at"].isoformat()
            if out.get("updated_at") is not None:
                out["updated_at"] = out["updated_at"].isoformat()
            return out
    finally:
        release_db_connection(conn)
