"""Роутер для работы с уведомлениями."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from database import get_db_connection, release_db_connection
from schemas import NotificationCreate, Notification, NotificationResponse


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("", response_model=Notification)
async def create_notification(
    notification: NotificationCreate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
):
    """Создает новое уведомление.
    
    Требует JWT аутентификации и роли admin.
    
    Args:
        notification: Данные уведомления
        x_user_id: ID пользователя из заголовка (добавляется api-gateway)
        x_user_role: Роль пользователя из заголовка (добавляется api-gateway)
    
    Returns:
        Notification: Созданное уведомление
    """
    # Проверка аутентификации
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    
    # Проверка роли admin
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create notifications")
    
    user_id = notification.user_id
    if user_id is None and x_user_id:
        try:
            user_id = int(x_user_id)
        except ValueError:
            user_id = None

    notif_type = notification.type or "general"

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO notifications (message, user_id, type)
                VALUES (%s, %s, %s)
                RETURNING id, message, user_id, type, created_at
                """,
                (notification.message, user_id, notif_type)
            )
            row = await cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create notification")
            
            return Notification(
                id=row[0],
                message=row[1],
                user_id=row[2],
                type=row[3] or "general",
                created_at=row[4]
            )
    finally:
        await release_db_connection(conn)


@router.get("", response_model=NotificationResponse)
async def get_notifications(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """Получает 5 самых свежих уведомлений для текущего пользователя.
    
    Возвращает уведомления, адресованные конкретному пользователю,
    а также общие уведомления (user_id IS NULL).
    Если X-User-Id не передан — возвращает только общие.
    
    Returns:
        NotificationResponse: Список уведомлений
    """
    caller_id: Optional[int] = None
    if x_user_id:
        try:
            caller_id = int(x_user_id)
        except ValueError:
            pass

    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            if caller_id is not None:
                await cur.execute(
                    """
                    SELECT id, message, user_id, type, created_at
                    FROM notifications
                    WHERE user_id = %s OR user_id IS NULL
                    ORDER BY created_at DESC
                    LIMIT 5
                    """,
                    (caller_id,)
                )
            else:
                await cur.execute(
                    """
                    SELECT id, message, user_id, type, created_at
                    FROM notifications
                    WHERE user_id IS NULL
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                )
            rows = await cur.fetchall()
            
            notifications = [
                Notification(
                    id=row[0],
                    message=row[1],
                    user_id=row[2],
                    type=row[3] or "general",
                    created_at=row[4]
                )
                for row in rows
            ]
            
            return NotificationResponse(notifications=notifications)
    finally:
        await release_db_connection(conn)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
):
    """Удаляет уведомление по ID.
    
    Требует JWT аутентификации и роли admin.
    
    Args:
        notification_id: ID уведомления для удаления
        x_user_id: ID пользователя из заголовка (добавляется api-gateway)
        x_user_role: Роль пользователя из заголовка (добавляется api-gateway)
    
    Returns:
        dict: Сообщение об успешном удалении
    """
    # Проверка аутентификации
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    
    # Проверка роли admin
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete notifications")
    
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM notifications WHERE id = %s RETURNING id",
                (notification_id,)
            )
            row = await cur.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Notification not found")
            
            return {"message": "Notification deleted successfully", "id": notification_id}
    finally:
        await release_db_connection(conn)
