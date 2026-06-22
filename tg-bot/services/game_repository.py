"""Доступ к данным игры (aiopg)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GameModeRow:
    id: int
    code: str
    title: str
    is_active: bool
    questions_per_game: int


@dataclass(slots=True)
class GameQuestionRow:
    id: int
    mode_id: int
    prompt_text: str
    image_file_id: Optional[str]
    image_url: Optional[str]


@dataclass(slots=True)
class GameOptionRow:
    id: int
    question_id: int
    option_index: int
    option_text: str
    is_correct: bool


@dataclass(slots=True)
class GameSessionRow:
    id: int
    player_id: int
    mode_id: int
    status: str
    score: int
    correct_count: int
    total_questions: int
    current_step: int


class GameRepository:
    """Репозиторий игровых сущностей."""

    async def get_telegram_user_id_for_player(self, player_id: int) -> Optional[int]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT telegram_user_id FROM game_players WHERE id = %s",
                    (player_id,),
                )
                r = await cur.fetchone()
                out = int(r[0]) if r else None
                await conn.commit()
                return out
        finally:
            await release_db_connection(conn)

    async def upsert_player(
        self,
        *,
        telegram_user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        is_admin: bool,
    ) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_players (telegram_user_id, username, first_name, is_admin)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (telegram_user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        is_admin = game_players.is_admin OR EXCLUDED.is_admin
                    RETURNING id
                    """,
                    (telegram_user_id, username, first_name, is_admin),
                )
                row = await cur.fetchone()
                await conn.commit()
                return int(row[0])
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def list_active_modes(self) -> list[GameModeRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, code, title, is_active, questions_per_game
                    FROM game_modes
                    WHERE is_active = TRUE
                    ORDER BY id
                    """
                )
                rows = await cur.fetchall()
                result = [
                    GameModeRow(
                        id=int(r[0]),
                        code=str(r[1]),
                        title=str(r[2]),
                        is_active=bool(r[3]),
                        questions_per_game=int(r[4]),
                    )
                    for r in rows
                ]
                await conn.commit()
                return result
        finally:
            await release_db_connection(conn)

    async def get_mode(self, mode_id: int) -> Optional[GameModeRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, code, title, is_active, questions_per_game
                    FROM game_modes WHERE id = %s
                    """,
                    (mode_id,),
                )
                r = await cur.fetchone()
                if not r:
                    await conn.commit()
                    return None
                row = GameModeRow(
                    id=int(r[0]),
                    code=str(r[1]),
                    title=str(r[2]),
                    is_active=bool(r[3]),
                    questions_per_game=int(r[4]),
                )
                await conn.commit()
                return row
        finally:
            await release_db_connection(conn)

    async def get_question_ids_ready_for_mode(self, mode_id: int) -> list[int]:
        """Вопросы с ровно 6 вариантами ответа."""
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT q.id
                    FROM game_questions q
                    WHERE q.mode_id = %s AND q.is_active = TRUE
                      AND (
                        SELECT COUNT(*) FROM game_question_options o
                        WHERE o.question_id = q.id
                      ) = 6
                    ORDER BY q.id
                    """,
                    (mode_id,),
                )
                rows = await cur.fetchall()
                out = [int(r[0]) for r in rows]
                await conn.commit()
                return out
        finally:
            await release_db_connection(conn)

    async def get_in_progress_session_for_player(self, player_id: int) -> Optional[GameSessionRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, player_id, mode_id, status, score, correct_count,
                           total_questions, current_step
                    FROM game_sessions
                    WHERE player_id = %s AND status = 'in_progress'
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (player_id,),
                )
                r = await cur.fetchone()
                if not r:
                    await conn.commit()
                    return None
                row = GameSessionRow(
                    id=int(r[0]),
                    player_id=int(r[1]),
                    mode_id=int(r[2]),
                    status=str(r[3]),
                    score=int(r[4]),
                    correct_count=int(r[5]),
                    total_questions=int(r[6]),
                    current_step=int(r[7]),
                )
                await conn.commit()
                return row
        finally:
            await release_db_connection(conn)

    async def create_session_with_questions(
        self,
        *,
        player_id: int,
        mode_id: int,
        ordered_question_ids: list[int],
    ) -> int:
        if not ordered_question_ids:
            raise ValueError("ordered_question_ids must not be empty")

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE game_sessions
                    SET status = 'aborted', finished_at = NOW()
                    WHERE player_id = %s AND status = 'in_progress'
                    """,
                    (player_id,),
                )
                await cur.execute(
                    """
                    INSERT INTO game_sessions (
                        player_id, mode_id, status, score, correct_count,
                        total_questions, current_step
                    )
                    VALUES (%s, %s, 'in_progress', 0, 0, %s, 0)
                    RETURNING id
                    """,
                    (player_id, mode_id, len(ordered_question_ids)),
                )
                row = await cur.fetchone()
                session_id = int(row[0])

                for step, qid in enumerate(ordered_question_ids):
                    await cur.execute(
                        """
                        INSERT INTO game_session_questions (session_id, step_index, question_id)
                        VALUES (%s, %s, %s)
                        """,
                        (session_id, step, qid),
                    )
                await conn.commit()
                return session_id
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def get_session(self, session_id: int) -> Optional[GameSessionRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, player_id, mode_id, status, score, correct_count,
                           total_questions, current_step
                    FROM game_sessions WHERE id = %s
                    """,
                    (session_id,),
                )
                r = await cur.fetchone()
                if not r:
                    await conn.commit()
                    return None
                row = GameSessionRow(
                    id=int(r[0]),
                    player_id=int(r[1]),
                    mode_id=int(r[2]),
                    status=str(r[3]),
                    score=int(r[4]),
                    correct_count=int(r[5]),
                    total_questions=int(r[6]),
                    current_step=int(r[7]),
                )
                await conn.commit()
                return row
        finally:
            await release_db_connection(conn)

    async def get_session_question_at_step(
        self, session_id: int, step: int
    ) -> Optional[int]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT question_id FROM game_session_questions
                    WHERE session_id = %s AND step_index = %s
                    """,
                    (session_id, step),
                )
                r = await cur.fetchone()
                qid = int(r[0]) if r else None
                await conn.commit()
                return qid
        finally:
            await release_db_connection(conn)

    async def get_question_with_options(
        self, question_id: int
    ) -> tuple[Optional[GameQuestionRow], list[GameOptionRow]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, mode_id, prompt_text, image_file_id, image_url
                    FROM game_questions WHERE id = %s
                    """,
                    (question_id,),
                )
                qr = await cur.fetchone()
                if not qr:
                    await conn.commit()
                    return None, []

                question = GameQuestionRow(
                    id=int(qr[0]),
                    mode_id=int(qr[1]),
                    prompt_text=str(qr[2]),
                    image_file_id=qr[3],
                    image_url=qr[4],
                )

                await cur.execute(
                    """
                    SELECT id, question_id, option_index, option_text, is_correct
                    FROM game_question_options
                    WHERE question_id = %s
                    ORDER BY option_index
                    """,
                    (question_id,),
                )
                opts = await cur.fetchall()
                options = [
                    GameOptionRow(
                        id=int(o[0]),
                        question_id=int(o[1]),
                        option_index=int(o[2]),
                        option_text=str(o[3]),
                        is_correct=bool(o[4]),
                    )
                    for o in opts
                ]
                await conn.commit()
                return question, options
        finally:
            await release_db_connection(conn)

    async def get_option(self, option_id: int) -> Optional[GameOptionRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, question_id, option_index, option_text, is_correct
                    FROM game_question_options WHERE id = %s
                    """,
                    (option_id,),
                )
                o = await cur.fetchone()
                if not o:
                    await conn.commit()
                    return None
                row = GameOptionRow(
                    id=int(o[0]),
                    question_id=int(o[1]),
                    option_index=int(o[2]),
                    option_text=str(o[3]),
                    is_correct=bool(o[4]),
                )
                await conn.commit()
                return row
        finally:
            await release_db_connection(conn)

    async def submit_answer_and_advance(
        self,
        *,
        session_id: int,
        question_id: int,
        selected_option_id: int,
        points_per_correct: int = 1,
    ) -> dict[str, Any]:
        """
        Идемпотентная фиксация ответа: при повторном callback ответ не меняется.
        Возвращает dict: inserted, is_correct, session_completed, score, correct_count, ...
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, status, score, correct_count, total_questions, current_step, started_at "
                    "FROM game_sessions WHERE id = %s FOR UPDATE",
                    (session_id,),
                )
                srow = await cur.fetchone()
                if not srow:
                    await conn.rollback()
                    return {"error": "session_not_found"}

                _sid, status, score, correct_count, total_questions, current_step, started_at = srow
                if status != "in_progress":
                    await conn.rollback()
                    return {"error": "session_not_active", "status": status}

                await cur.execute(
                    """
                    SELECT question_id FROM game_session_questions
                    WHERE session_id = %s AND step_index = %s
                    """,
                    (session_id, current_step),
                )
                expected_q = await cur.fetchone()
                if not expected_q or int(expected_q[0]) != question_id:
                    await conn.rollback()
                    return {"error": "wrong_question_for_step"}

                await cur.execute(
                    """
                    INSERT INTO game_answers (session_id, question_id, selected_option_id, is_correct)
                    SELECT %s, %s, %s, o.is_correct
                    FROM game_question_options o
                    WHERE o.id = %s AND o.question_id = %s
                    ON CONFLICT (session_id, question_id) DO NOTHING
                    RETURNING id, is_correct
                    """,
                    (session_id, question_id, selected_option_id, selected_option_id, question_id),
                )
                ins = await cur.fetchone()

                if not ins:
                    await cur.execute(
                        """
                        SELECT is_correct FROM game_answers
                        WHERE session_id = %s AND question_id = %s
                        """,
                        (session_id, question_id),
                    )
                    prev = await cur.fetchone()
                    is_correct = bool(prev[0]) if prev else False
                    await conn.rollback()
                    return {
                        "inserted": False,
                        "is_correct": is_correct,
                        "duplicate": True,
                        "current_step": current_step,
                        "total_questions": total_questions,
                    }

                is_correct = bool(ins[1])
                new_score = int(score) + (points_per_correct if is_correct else 0)
                new_correct = int(correct_count) + (1 if is_correct else 0)
                new_step = int(current_step) + 1
                completed = new_step >= int(total_questions)

                if completed:
                    finished_at = datetime.now(timezone.utc)
                    if started_at:
                        if hasattr(started_at, "timestamp"):
                            duration_sec = max(
                                0,
                                int((finished_at - started_at).total_seconds()),
                            )
                        else:
                            duration_sec = None
                    else:
                        duration_sec = None

                    await cur.execute(
                        """
                        UPDATE game_sessions
                        SET score = %s, correct_count = %s, current_step = %s,
                            status = 'completed', finished_at = %s, duration_sec = %s
                        WHERE id = %s
                        """,
                        (
                            new_score,
                            new_correct,
                            new_step,
                            finished_at,
                            duration_sec,
                            session_id,
                        ),
                    )
                else:
                    await cur.execute(
                        """
                        UPDATE game_sessions
                        SET score = %s, correct_count = %s, current_step = %s
                        WHERE id = %s
                        """,
                        (new_score, new_correct, new_step, session_id),
                    )

                await conn.commit()
                return {
                    "inserted": True,
                    "is_correct": is_correct,
                    "duplicate": False,
                    "session_completed": completed,
                    "score": new_score,
                    "correct_count": new_correct,
                    "current_step": new_step,
                    "total_questions": total_questions,
                }
        except Exception as e:
            logger.exception("submit_answer_and_advance failed: %s", e)
            try:
                await conn.rollback()
            except Exception:
                pass
            raise
        finally:
            await release_db_connection(conn)

    async def fetch_leaderboard(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """
        Лучшая завершённая сессия на игрока: max(score), tie-break — меньший duration_sec,
        затем более ранний finished_at.
        """
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    WITH ranked_sessions AS (
                        SELECT
                            gs.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY gs.player_id
                                ORDER BY gs.score DESC,
                                    gs.duration_sec ASC NULLS LAST,
                                    gs.finished_at ASC NULLS LAST
                            ) AS rn
                        FROM game_sessions gs
                        WHERE gs.status = 'completed'
                    )
                    SELECT p.telegram_user_id, p.username, rs.score, rs.duration_sec, rs.finished_at
                    FROM ranked_sessions rs
                    JOIN game_players p ON p.id = rs.player_id
                    WHERE rs.rn = 1
                    ORDER BY rs.score DESC, rs.duration_sec ASC NULLS LAST, rs.finished_at ASC NULLS LAST
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
                result = [
                    {
                        "telegram_user_id": int(r[0]),
                        "username": r[1],
                        "score": int(r[2]),
                        "duration_sec": r[3],
                        "finished_at": r[4].isoformat() if r[4] else None,
                    }
                    for r in rows
                ]
                await conn.commit()
                return result
        finally:
            await release_db_connection(conn)

    # --- Admin CRUD ---

    async def admin_create_mode(
        self,
        *,
        code: str,
        title: str,
        questions_per_game: int,
        is_active: bool = True,
    ) -> int:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_modes (code, title, is_active, questions_per_game)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (code, title, is_active, questions_per_game),
                )
                row = await cur.fetchone()
                await conn.commit()
                return int(row[0])
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def admin_list_modes(self, *, include_inactive: bool = True) -> list[GameModeRow]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                if include_inactive:
                    await cur.execute(
                        """
                        SELECT id, code, title, is_active, questions_per_game
                        FROM game_modes ORDER BY id
                        """
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, code, title, is_active, questions_per_game
                        FROM game_modes WHERE is_active = TRUE ORDER BY id
                        """
                    )
                rows = await cur.fetchall()
                result = [
                    GameModeRow(
                        id=int(r[0]),
                        code=str(r[1]),
                        title=str(r[2]),
                        is_active=bool(r[3]),
                        questions_per_game=int(r[4]),
                    )
                    for r in rows
                ]
                await conn.commit()
                return result
        finally:
            await release_db_connection(conn)

    async def admin_update_mode(
        self,
        mode_id: int,
        *,
        title: Optional[str] = None,
        is_active: Optional[bool] = None,
        questions_per_game: Optional[int] = None,
    ) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                fields: list[str] = []
                vals: list[Any] = []
                if title is not None:
                    fields.append("title = %s")
                    vals.append(title)
                if is_active is not None:
                    fields.append("is_active = %s")
                    vals.append(is_active)
                if questions_per_game is not None:
                    fields.append("questions_per_game = %s")
                    vals.append(questions_per_game)
                if not fields:
                    await conn.commit()
                    return True
                vals.append(mode_id)
                await cur.execute(
                    f"UPDATE game_modes SET {', '.join(fields)} WHERE id = %s",
                    vals,
                )
                await conn.commit()
                return True
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def admin_list_questions(self, mode_id: int) -> list[dict[str, Any]]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, mode_id, prompt_text, image_file_id, image_url, is_active
                    FROM game_questions WHERE mode_id = %s ORDER BY id
                    """,
                    (mode_id,),
                )
                rows = await cur.fetchall()
                result = [
                    {
                        "id": int(r[0]),
                        "mode_id": int(r[1]),
                        "prompt_text": str(r[2]),
                        "image_file_id": r[3],
                        "image_url": r[4],
                        "is_active": bool(r[5]),
                    }
                    for r in rows
                ]
                await conn.commit()
                return result
        finally:
            await release_db_connection(conn)

    async def admin_create_question_with_options(
        self,
        *,
        mode_id: int,
        prompt_text: str,
        image_file_id: Optional[str],
        image_url: Optional[str],
        options: list[dict[str, Any]],
    ) -> int:
        if len(options) != 6:
            raise ValueError("Exactly 6 options required")

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO game_questions (mode_id, prompt_text, image_file_id, image_url, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (mode_id, prompt_text, image_file_id, image_url),
                )
                row = await cur.fetchone()
                qid = int(row[0])

                for opt in options:
                    await cur.execute(
                        """
                        INSERT INTO game_question_options
                        (question_id, option_index, option_text, is_correct)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            qid,
                            int(opt["option_index"]),
                            str(opt["option_text"]),
                            bool(opt["is_correct"]),
                        ),
                    )
                await conn.commit()
                return qid
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def admin_update_question(
        self,
        question_id: int,
        *,
        prompt_text: Optional[str] = None,
        image_file_id: Optional[str] = None,
        image_url: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                fields: list[str] = []
                vals: list[Any] = []
                if prompt_text is not None:
                    fields.append("prompt_text = %s")
                    vals.append(prompt_text)
                if image_file_id is not None:
                    fields.append("image_file_id = %s")
                    vals.append(image_file_id)
                if image_url is not None:
                    fields.append("image_url = %s")
                    vals.append(image_url)
                if is_active is not None:
                    fields.append("is_active = %s")
                    vals.append(is_active)
                if not fields:
                    await conn.commit()
                    return True
                vals.append(question_id)
                await cur.execute(
                    f"UPDATE game_questions SET {', '.join(fields)} WHERE id = %s",
                    vals,
                )
                await conn.commit()
                return True
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)

    async def admin_replace_question_options(
        self, question_id: int, options: list[dict[str, Any]]
    ) -> None:
        if len(options) != 6:
            raise ValueError("Exactly 6 options required")

        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM game_question_options WHERE question_id = %s",
                    (question_id,),
                )
                for opt in options:
                    await cur.execute(
                        """
                        INSERT INTO game_question_options
                        (question_id, option_index, option_text, is_correct)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            question_id,
                            int(opt["option_index"]),
                            str(opt["option_text"]),
                            bool(opt["is_correct"]),
                        ),
                    )
                await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await release_db_connection(conn)


game_repository = GameRepository()
