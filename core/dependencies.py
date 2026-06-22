"""Зависимости для проверки авторизации и ролей."""

import jwt
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from config import settings


security = HTTPBearer()


def get_current_user(
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
        HTTPException: Если токен невалидный или отсутствует
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

        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "guest")
        }
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
    current_user = get_current_user(request, credentials)
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    return current_user
