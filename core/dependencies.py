"""Зависимости для проверки авторизации и ролей."""

import jwt
import httpx
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from config import settings


security = HTTPBearer()


def _internal_headers() -> dict[str, str]:
    token = (getattr(settings, "INTERNAL_API_TOKEN", None) or "").strip()
    if token:
        return {"X-Internal-Token": token}
    return {}


async def is_token_blacklisted(token: str) -> bool:
    """Проверяет blacklist через auth-сервис (fail closed при ошибке связи)."""
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/token/blacklist-check"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url, json={"token": token}, headers=_internal_headers()
            )
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


def _iat_as_epoch(iat_value) -> Optional[int]:
    if iat_value is None:
        return None
    if isinstance(iat_value, (int, float)):
        return int(iat_value)
    try:
        return int(iat_value.timestamp())
    except Exception:
        return None


async def _tokens_valid_after_epoch(user_id: int) -> Optional[int]:
    from shared.token_blacklist_redis import token_blacklist_redis

    redis_value = await token_blacklist_redis.get_tokens_valid_after(user_id)
    if redis_value is not None:
        return redis_value
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/token/valid-after/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=_internal_headers())
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to verify token validity cutoff",
            )
        data = response.json()
        raw = data.get("tokens_valid_after_epoch")
        return int(raw) if raw is not None else None
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token validity cutoff",
        ) from error


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Dict:
    """Получение текущего пользователя из JWT токена."""
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
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
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

        user_id = payload.get("user_id")
        if user_id is not None:
            cutoff = await _tokens_valid_after_epoch(int(user_id))
            iat_epoch = _iat_as_epoch(payload.get("iat"))
            if cutoff is not None and (iat_epoch is None or iat_epoch < cutoff):
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
    """Получение текущего пользователя с проверкой роли admin."""
    current_user = await get_current_user(request, credentials)
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    return current_user
