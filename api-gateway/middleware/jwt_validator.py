import jwt
import httpx
from typing import Optional
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings, PUBLIC_ENDPOINTS, PUBLIC_PATH_PREFIXES
from utils.exceptions import TokenValidationException


class JwtValidator:
    """Валидатор JWT токенов."""
    
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def decode_token(self, token: str, *, audience: str | None = None) -> dict:
        """Декодирует JWT токен.
        
        Args:
            token: JWT токен
            audience: если задан — проверяет aud; иначе aud не проверяется
                (токены CopyParse без aud)
        
        Returns:
            Декодированные данные токена (payload)
        
        Raises:
            TokenValidationException: Если токен невалидный или истек
        """
        try:
            kwargs: dict = {
                "algorithms": [self.algorithm],
                "options": {"verify_aud": bool(audience)},
            }
            if audience:
                kwargs["audience"] = audience
            return jwt.decode(token, self.secret_key, **kwargs)
        except jwt.ExpiredSignatureError as error:
            raise TokenValidationException("Token has expired.") from error
        except jwt.InvalidTokenError as error:
            raise TokenValidationException("Invalid token.") from error
    
    def validate_token(self, token: str) -> bool:
        """Валидирует JWT токен.
        
        Args:
            token: JWT токен
        
        Returns:
            True если токен валидный
        
        Raises:
            TokenValidationException: Если токен невалидный
        """
        self.decode_token(token)
        return True
    
    def extract_token_from_header(self, authorization_header: Optional[str]) -> str:
        """Извлекает токен из Authorization header.
        
        Args:
            authorization_header: Значение Authorization header
        
        Returns:
            JWT токен без префикса Bearer
        
        Raises:
            TokenValidationException: Если header отсутствует или неверного формата
        """
        if not authorization_header:
            raise TokenValidationException("Authorization header is missing.")
        
        parts = authorization_header.split()
        
        if len(parts) != 2:
            raise TokenValidationException("Invalid authorization header format.")
        
        scheme, token = parts
        
        if scheme.lower() != "bearer":
            raise TokenValidationException("Invalid authentication scheme. Use Bearer.")
        
        return token
    
    def get_user_from_token(self, token: str) -> dict:
        """Получает данные пользователя из токена.
        
        Args:
            token: JWT токен
        
        Returns:
            Словарь с данными пользователя из токена
        """
        # verify_aud=False: токены CopyParse без aud
        payload = self.decode_token(token)
        token_type = payload.get("type")

        if token_type != "access":
            raise TokenValidationException("Invalid token type. Access token required.")
        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "type": token_type,
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
        }


# Глобальный экземпляр JwtValidator
jwt_validator = JwtValidator(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM
)


# HTTP Bearer security scheme для OpenAPI документации
security_scheme = HTTPBearer(auto_error=False)


def check_public_endpoint(endpoint_path: str) -> bool:
    """Проверяет, является ли endpoint публичным (не требует JWT).
    
    Args:
        endpoint_path: Путь endpoint'а
    
    Returns:
        True если endpoint публичный
    """
    if endpoint_path in PUBLIC_ENDPOINTS:
        return True
    for prefix in PUBLIC_PATH_PREFIXES:
        if endpoint_path.startswith(prefix):
            return True
    return False


async def _blacklist_via_auth_http(
    token: str, http_client: Optional[httpx.AsyncClient] = None
) -> bool:
    """Fallback: auth Postgres-backed blacklist-check (fail closed)."""
    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/token/blacklist-check"
    headers = {}
    internal = (settings.INTERNAL_API_TOKEN or "").strip()
    if internal:
        headers["X-Internal-Token"] = internal
    try:
        if http_client is not None:
            response = await http_client.post(
                url, json={"token": token}, headers=headers, timeout=5.0
            )
        else:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json={"token": token}, headers=headers)
        if response.status_code != 200:
            raise TokenValidationException("Unable to verify token revocation status.")
        data = response.json()
        return bool(data.get("blacklisted"))
    except TokenValidationException:
        raise
    except Exception as error:
        raise TokenValidationException(
            "Unable to verify token revocation status."
        ) from error


async def is_token_blacklisted(token: str, http_client: Optional[httpx.AsyncClient] = None) -> bool:
    """Проверяет blacklist: Redis (если warm) → HTTP auth (fail closed)."""
    from shared.token_blacklist_redis import token_blacklist_redis

    ready = await token_blacklist_redis.is_ready()
    if ready is True:
        hit = await token_blacklist_redis.contains(token)
        if hit is not None:
            return hit

    return await _blacklist_via_auth_http(token, http_client)


def _iat_as_epoch(iat_value) -> Optional[int]:
    if iat_value is None:
        return None
    if isinstance(iat_value, (int, float)):
        return int(iat_value)
    try:
        return int(iat_value.timestamp())
    except Exception:
        return None


async def _tokens_valid_after_epoch(
    user_id: int, http_client: Optional[httpx.AsyncClient] = None
) -> Optional[int]:
    """Earliest acceptable JWT iat for user; None if no cutoff."""
    from shared.token_blacklist_redis import token_blacklist_redis

    redis_value = await token_blacklist_redis.get_tokens_valid_after(user_id)
    if redis_value is not None:
        return redis_value

    url = f"{settings.AUTH_SERVICE_URL.rstrip('/')}/token/valid-after/{user_id}"
    headers = {}
    internal = (settings.INTERNAL_API_TOKEN or "").strip()
    if internal:
        headers["X-Internal-Token"] = internal
    try:
        if http_client is not None:
            response = await http_client.get(url, headers=headers, timeout=5.0)
        else:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise TokenValidationException("Unable to verify token validity cutoff.")
        data = response.json()
        raw = data.get("tokens_valid_after_epoch")
        if raw is None:
            return None
        return int(raw)
    except TokenValidationException:
        raise
    except Exception as error:
        raise TokenValidationException(
            "Unable to verify token validity cutoff."
        ) from error


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[dict]:
    """Dependency для получения текущего пользователя из JWT.
    
    Для публичных endpoints возвращает None без ошибки.
    Для защищенных endpoints требует валидный JWT и отсутствие в blacklist.
    """
    endpoint_path = request.url.path
    
    if check_public_endpoint(endpoint_path):
        return None
    
    if not credentials:
        raise TokenValidationException("Authorization header is required.")
    
    token = credentials.credentials
    user = jwt_validator.get_user_from_token(token)

    http_client = getattr(request.app.state, "http_client", None)
    if await is_token_blacklisted(token, http_client):
        raise TokenValidationException("Token has been revoked")

    user_id = user.get("user_id")
    if user_id is not None:
        cutoff = await _tokens_valid_after_epoch(int(user_id), http_client)
        iat_epoch = _iat_as_epoch(user.get("iat"))
        if cutoff is not None and (iat_epoch is None or iat_epoch < cutoff):
            raise TokenValidationException("Token has been revoked")

    return user


async def validate_jwt_middleware(request: Request) -> Optional[dict]:
    """Валидирует JWT из запроса (для использования в middleware)."""
    endpoint_path = request.url.path
    
    if check_public_endpoint(endpoint_path):
        return None
    
    authorization_header = request.headers.get("authorization")
    
    if not authorization_header:
        raise TokenValidationException("Authorization header is required.")
    
    token = jwt_validator.extract_token_from_header(authorization_header)
    user = jwt_validator.get_user_from_token(token)

    http_client = getattr(request.app.state, "http_client", None)
    if await is_token_blacklisted(token, http_client):
        raise TokenValidationException("Token has been revoked")

    user_id = user.get("user_id")
    if user_id is not None:
        cutoff = await _tokens_valid_after_epoch(int(user_id), http_client)
        iat_epoch = _iat_as_epoch(user.get("iat"))
        if cutoff is not None and (iat_epoch is None or iat_epoch < cutoff):
            raise TokenValidationException("Token has been revoked")

    return user
