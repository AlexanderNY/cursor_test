"""Роутер для работы с обратной связью."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from database import get_db_connection, release_db_connection
from schemas import FeedbackCreate, Feedback, FeedbackResponse


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=Feedback)
async def create_feedback(
    feedback: FeedbackCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
) -> Feedback:
    """Создаёт новую запись обратной связи.

    Требует JWT аутентификации.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")

    user_id: Optional[int] = None
    try:
        user_id = int(x_user_id)
    except ValueError:
        pass

    email = str(feedback.email) if feedback.email else None

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO feedback (type, text, email, user_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, type, text, email, user_id, created_at
                """,
                (feedback.type, feedback.text, email, user_id),
            )
            row = await cur.fetchone()

            if not row:
                raise HTTPException(status_code=500, detail="Failed to create feedback")

            return Feedback(
                id=row[0],
                type=row[1],
                text=row[2],
                email=row[3],
                user_id=row[4],
                created_at=row[5],
            )
    finally:
        await release_db_connection(conn)


@router.get("", response_model=FeedbackResponse)
async def get_feedback_list(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> FeedbackResponse:
    """Получает все записи обратной связи. Только для admin."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")

    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view feedback")

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id, type, text, email, user_id, created_at
                FROM feedback
                ORDER BY created_at DESC
                """
            )
            rows = await cur.fetchall()

            feedback_list = [
                Feedback(
                    id=row[0],
                    type=row[1],
                    text=row[2],
                    email=row[3],
                    user_id=row[4],
                    created_at=row[5],
                )
                for row in rows
            ]

            return FeedbackResponse(feedback=feedback_list)
    finally:
        await release_db_connection(conn)


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> dict:
    """Удаляет запись обратной связи по ID. Только для admin."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")

    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete feedback")

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM feedback WHERE id = %s RETURNING id",
                (feedback_id,),
            )
            row = await cur.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Feedback not found")

            return {"message": "Feedback deleted successfully", "id": feedback_id}
    finally:
        await release_db_connection(conn)
