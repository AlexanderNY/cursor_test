import jwt
from datetime import datetime, timedelta
from typing import Dict
from config import settings
from utils.exceptions import TokenExpiredError, TokenInvalidError


def create_access_token(user_id: int, role: str = "guest", is_blocked: bool = False) -> str:
    """Создание access токена для пользователя."""
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "role": role,
        "is_blocked": bool(is_blocked),
        "type": "access",
        "iat": now,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int, role: str = "guest") -> str:
    """Создание refresh токена для пользователя."""
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict:
    """Декодирование JWT токена."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError:
        raise TokenInvalidError("Invalid token")


def create_email_verification_token(user_id: int) -> str:
    """Создание токена для верификации email."""
    expire = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "type": "email_verification",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(user_id: int) -> str:
    """Создание токена для сброса пароля."""
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "type": "password_reset",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

