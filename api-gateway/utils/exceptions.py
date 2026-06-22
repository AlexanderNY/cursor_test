from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class GatewayException(Exception):
    """Базовое исключение API Gateway."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitExceededException(GatewayException):
    """Превышен лимит запросов."""
    
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message=message, status_code=429)


class TokenValidationException(GatewayException):
    """Ошибка валидации токена."""
    
    def __init__(self, message: str = "Invalid or expired token."):
        super().__init__(message=message, status_code=401)


class ServiceUnavailableException(GatewayException):
    """Целевой сервис недоступен (нет соединения, таймаут и т.д.)."""

    def __init__(self, service_name: str = "unknown", detail: Optional[str] = None):
        if detail:
            message = detail
        else:
            message = f"Service '{service_name}' is currently unavailable."
        super().__init__(message=message, status_code=503)


class BadGatewayException(GatewayException):
    """Ошибка при проксировании запроса."""
    
    def __init__(self, message: str = "Bad gateway. Error communicating with upstream service."):
        super().__init__(message=message, status_code=502)


def create_error_response(status_code: int, detail: str) -> JSONResponse:
    """Создает JSON ответ с ошибкой."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "detail": detail,
            "status_code": status_code
        }
    )


def handle_gateway_exception(request: Request, exc: GatewayException) -> JSONResponse:
    """Обрабатывает исключения gateway и возвращает JSON ответ."""
    return create_error_response(
        status_code=exc.status_code,
        detail=exc.message
    )


