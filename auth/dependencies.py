from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from utils.jwt_utils import decode_token
from services.token_service import is_token_blacklisted, get_tokens_valid_after_epoch
from services.auth_service import get_user_by_id
from utils.exceptions import TokenExpiredError, TokenInvalidError

security = HTTPBearer()


def _iat_as_epoch(iat_value) -> int | None:
    if iat_value is None:
        return None
    if isinstance(iat_value, (int, float)):
        return int(iat_value)
    try:
        return int(iat_value.timestamp())
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """Получение текущего пользователя из JWT токена."""
    token = credentials.credentials
    
    # Проверка blacklist
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = decode_token(token)
        
        # Проверка типа токена
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        cutoff = await get_tokens_valid_after_epoch(int(user_id))
        iat_epoch = _iat_as_epoch(payload.get("iat"))
        if cutoff is not None and (iat_epoch is None or iat_epoch < cutoff):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Получение пользователя из базы данных
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        if user.get("is_blocked"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been blocked"
            )
        
        return user
    except HTTPException:
        raise
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_admin_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Получение текущего пользователя с проверкой роли admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user

