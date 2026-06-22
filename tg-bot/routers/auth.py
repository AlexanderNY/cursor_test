"""Роутер для авторизации Telegram."""

import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from schemas import PhoneCodeRequest, PasswordRequest, AuthResponse, AuthStatusResponse
from services.auth_handler import auth_handler
from services.client_manager import TelegramClientManager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Telegram Auth"])

# Глобальный менеджер клиентов (будет инициализирован в main.py)
client_manager: Optional[TelegramClientManager] = None


def set_client_manager(manager: TelegramClientManager) -> None:
    """Устанавливает менеджер клиентов для роутера.
    
    Args:
        manager: TelegramClientManager
    """
    global client_manager
    client_manager = manager


@router.post("/code", response_model=AuthResponse)
async def submit_phone_code(request: PhoneCodeRequest):
    """Обрабатывает код подтверждения от пользователя.
    
    Args:
        request: Запрос с кодом подтверждения
        
    Returns:
        Результат авторизации
    """
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")
    
    # Получаем клиент ожидающий авторизации
    client = client_manager.get_pending_client(request.user_id)
    
    if not client:
        raise HTTPException(
            status_code=404,
            detail="No pending authorization found for this user"
        )
    
    # Обрабатываем код
    result = await auth_handler.submit_phone_code(
        request.user_id,
        request.code,
        client
    )
    
    if result.get("success"):
        # Перемещаем клиент в активные
        client_manager.move_client_to_active(request.user_id)
    
    return AuthResponse(**result)


@router.post("/password", response_model=AuthResponse)
async def submit_password(request: PasswordRequest):
    """Обрабатывает 2FA пароль от пользователя.
    
    Args:
        request: Запрос с паролем
        
    Returns:
        Результат авторизации
    """
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")
    
    # Получаем клиент ожидающий авторизации
    client = client_manager.get_pending_client(request.user_id)
    
    if not client:
        raise HTTPException(
            status_code=404,
            detail="No pending authorization found for this user"
        )
    
    # Обрабатываем пароль
    result = await auth_handler.submit_2fa_password(
        request.user_id,
        request.password,
        client
    )
    
    if result.get("success"):
        # Перемещаем клиент в активные
        client_manager.move_client_to_active(request.user_id)
    
    return AuthResponse(**result)


@router.get("/status/{user_id}", response_model=AuthStatusResponse)
async def get_auth_status(user_id: int):
    """Получает статус авторизации пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Статус авторизации
    """
    from database import get_db_connection, release_db_connection
    
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT auth_state, auth_phone_number
                FROM tg_profiles
                WHERE user_id = %s
                """,
                (user_id,)
            )
            row = await cur.fetchone()
            
            if not row:
                logger.warning("Profile not found for user_id=%s (tg_profiles has no row)", user_id)
                raise HTTPException(status_code=404, detail="Profile not found")
            
            auth_state, phone_number = row
            
            message = "Authorized"
            if auth_state == 'pending_code':
                message = f"Waiting for authorization code for {phone_number or 'phone'}"
            elif auth_state == 'pending_password':
                message = "Waiting for 2FA password"
            elif auth_state == 'failed':
                message = "Authorization failed"
            
            return AuthStatusResponse(
                user_id=user_id,
                auth_state=auth_state or 'unknown',
                message=message
            )
    finally:
        await release_db_connection(conn)
