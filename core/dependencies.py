"""Зависимости для проверки авторизации и ролей."""

import jwt
import httpx
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from config import settings


security = HTTPBearer()


async def is_token_blacklisted(token: str) -> bool:
    """Проверяет blacklist через auth-сервис (fail closed при ошибке связи)."""
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/token/blacklist-check"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"token": token})
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify token revocation status",
            )
        data = response.json()
        return bool(data.get("blacklisted"))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token revocation status",
        ) from error


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Dict:
    """Получение текущего пользователя из JWT токена.
    
    Args:
        request: FastAPI Request объект
        credentials: HTTP Authorization credentials
        
    Returns:
        Dict с данными пользователя из токена
        
    Raises:
        HTTPException: Если токен невалидный, отозван или отсутствует
    """
    # Пытаемся получить токен из credentials или из заголовков
    token = None
    if credentials:
        token = credentials.credentials
    else:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required"
        )
    
    try:
        # Декодируем токен
        # Используем секретный ключ из auth сервиса (должен быть одинаковый)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Проверяем тип токена
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        if payload.get("is_blocked") is True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been blocked"
            )

        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "guest")
        }
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_admin_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """Получение текущего пользователя с проверкой роли admin.
    
    Args:
        request: FastAPI Request объект
        credentials: HTTP Authorization credentials
        
    Returns:
        Dict с данными пользователя
        
    Raises:
        HTTPException: Если пользователь не авторизован или не является admin
    """
    current_user = await get_current_user(request, credentials)
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    return current_user
