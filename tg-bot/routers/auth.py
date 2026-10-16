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


def _assert_header_matches_user(
    x_user_id: Optional[str],
    body_user_id: int,
) -> None:
    if not x_user_id or not str(x_user_id).strip():
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        header_uid = int(x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id") from exc
    if header_uid != int(body_user_id):
        raise HTTPException(status_code=403, detail="Access denied for this user_id")


@router.post("/code", response_model=AuthResponse)
async def submit_phone_code(
    request: PhoneCodeRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """Обрабатывает код подтверждения от пользователя."""
    _assert_header_matches_user(x_user_id, request.user_id)
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")
    
    # Получаем клиент ожидающий авторизации
    client = client_manager.get_pending_client(request.user_id)
    
    if not client:
        raise HTTPException(
            status_code=404,
            detail=(
                "No pending Telegram session for this user. "
                "Connection to Telegram may have failed — set SOCKS5/HTTP proxy "
                "in the Telegram profile, save, and request a new code."
            ),
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


@router.post("/resend-code/{user_id}", response_model=AuthResponse)
async def resend_phone_code(user_id: int):
    """Повторно запрашивает код подтверждения. Не чаще одного раза в 120 секунд."""
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")

    result = await client_manager.resend_authorization_code(user_id)
    return AuthResponse(**result)


@router.post("/password", response_model=AuthResponse)
async def submit_password(
    request: PasswordRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """Обрабатывает 2FA пароль от пользователя."""
    _assert_header_matches_user(x_user_id, request.user_id)
    if not client_manager:
        raise HTTPException(status_code=503, detail="Client manager not initialized")
    
    # Получаем клиент ожидающий авторизации
    client = client_manager.get_pending_client(request.user_id)
    
    if not client:
        raise HTTPException(
            status_code=404,
            detail=(
                "No pending Telegram session for this user. "
                "Connection to Telegram may have failed — set SOCKS5/HTTP proxy "
                "in the Telegram profile, save, and try again."
            ),
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

    # Живой клиент важнее устаревшего auth_state в БД
    # (например failed после сетевой ошибки при уже валидной сессии).
    if client_manager and client_manager.get_client(user_id):
        if client_manager.get_pending_client(user_id) is None:
            return AuthStatusResponse(
                user_id=user_id,
                auth_state="authorized",
                message="Authorized",
            )
    
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
