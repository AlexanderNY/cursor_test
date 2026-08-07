from fastapi import APIRouter, HTTPException, status, Depends, Request
from schemas import (
    PasswordResetRequest,
    PasswordResetConfirm,
    TokenVerifyRequest,
    TokenVerifyResponse,
    TokenBlacklistCheckRequest,
    TokenBlacklistCheckResponse,
)
from services.auth_service import (
    verify_email_token,
    reset_password,
    initiate_password_reset
)
from services.token_service import is_token_blacklisted, blacklist_token
from utils.jwt_utils import decode_token
from utils.exceptions import (
    TokenNotFoundError,
    EmailAlreadyVerifiedError,
    TokenExpiredError,
    TokenInvalidError
)
from dependencies import get_current_user
from services.token_service import revoke_all_refresh_tokens
from typing import Dict


router = APIRouter(tags=["security"])


@router.get("/verify/{token}", status_code=status.HTTP_200_OK)
async def verify_email(token: str) -> Dict:
    """Верификация email по токену."""
    try:
        await verify_email_token(token)
        return {"message": "Email successfully verified"}
    except TokenNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EmailAlreadyVerifiedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_token(request: TokenVerifyRequest) -> TokenVerifyResponse:
    """Валидация токена для других микросервисов."""
    token = request.token
    
    # Проверка blacklist
    if await is_token_blacklisted(token):
        return TokenVerifyResponse(valid=False, user_id=None)
    
    try:
        payload = decode_token(token)
        
        # Проверка типа токена (должен быть access)
        if payload.get("type") != "access":
            return TokenVerifyResponse(valid=False, user_id=None)
        
        user_id = payload.get("user_id")
        if not user_id:
            return TokenVerifyResponse(valid=False, user_id=None)
        
        return TokenVerifyResponse(valid=True, user_id=user_id)
    except (TokenExpiredError, TokenInvalidError):
        return TokenVerifyResponse(valid=False, user_id=None)


@router.post("/token/blacklist-check", response_model=TokenBlacklistCheckResponse)
async def token_blacklist_check(
    request: TokenBlacklistCheckRequest,
) -> TokenBlacklistCheckResponse:
    """Проверка, отозван ли access-токен (для gateway/core)."""
    is_blacklisted = await is_token_blacklisted(request.token)
    return TokenBlacklistCheckResponse(blacklisted=is_blacklisted)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(request: PasswordResetRequest) -> Dict:
    """Запрос на сброс пароля (инициация)."""
    reset_token = await initiate_password_reset(request.email)
    
    # Всегда возвращаем успех для безопасности (не раскрываем существование пользователя)
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/reset-password/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(request: PasswordResetConfirm) -> Dict:
    """Подтверждение сброса пароля."""
    try:
        await reset_password(request.token, request.new_password)
        return {"message": "Password successfully reset"}
    except TokenNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/all_logout", status_code=status.HTTP_200_OK)
async def logout_all(
    http_request: Request,
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """Выход со всех устройств (отзыв всех refresh + blacklist текущего access)."""
    user_id = current_user["id"]
    await revoke_all_refresh_tokens(user_id)

    authorization = http_request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.split(" ", 1)[1]
        await blacklist_token(access_token)

    return {"message": "Successfully logged out from all devices"}
