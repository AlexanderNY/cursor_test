from fastapi import APIRouter, HTTPException, status, Depends, Request
from schemas import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest
from services.auth_service import register_user, authenticate_user, get_user_by_id
from services.token_service import (
    is_refresh_token_valid,
    revoke_refresh_token,
    blacklist_token,
    save_refresh_token
)
from utils.jwt_utils import create_access_token, create_refresh_token, decode_token
from utils.exceptions import (
    UserAlreadyExistsError,
    TokenExpiredError,
    TokenInvalidError
)
from dependencies import get_current_user
from typing import Dict


router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister) -> TokenResponse:
    """Регистрация нового пользователя."""
    try:
        result = await register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type="bearer"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin) -> TokenResponse:
    """Вход пользователя."""
    result = await authenticate_user(
        username=user_data.username,
        password=user_data.password
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer"
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    """Обновление пары токенов."""
    refresh_token = request.refresh_token
    
    # Проверка валидности refresh токена
    if not await is_refresh_token_valid(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    try:
        # Декодирование токена для получения user_id
        payload = decode_token(refresh_token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Получение пользователя для актуальной роли
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        if user.get("is_blocked"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account has been blocked"
            )
        
        user_role = user.get("role", "guest")
        blocked = bool(user.get("is_blocked", False))
        
        # Отзыв старого refresh токена
        await revoke_refresh_token(refresh_token)
        
        # Создание новой пары токенов с актуальной ролью
        new_access_token = create_access_token(user_id, user_role, is_blocked=blocked)
        new_refresh_token = create_refresh_token(user_id, user_role)
        
        # Сохранение нового refresh токена
        await save_refresh_token(user_id, new_refresh_token)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

# todo разобраться как реализовать разлогин - можно по токену, можно по id
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: RefreshTokenRequest,
    http_request: Request,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Выход пользователя."""
    refresh_token = request.refresh_token
    
    # Отзыв refresh токена
    await revoke_refresh_token(refresh_token)
    
    # Добавление access токена в blacklist
    authorization = http_request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        access_token = authorization.split(" ")[1]
        await blacklist_token(access_token)
    
    return {"message": "Successfully logged out"}

