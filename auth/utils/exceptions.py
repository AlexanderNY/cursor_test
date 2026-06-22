"""Кастомные исключения для обработки ошибок."""


class AuthException(Exception):
    """Базовое исключение для ошибок аутентификации."""
    pass


class InvalidCredentialsError(AuthException):
    """Ошибка неверных учетных данных."""
    pass


class TokenExpiredError(AuthException):
    """Ошибка истечения срока действия токена."""
    pass


class TokenInvalidError(AuthException):
    """Ошибка невалидного токена."""
    pass


class UserNotFoundError(AuthException):
    """Ошибка пользователь не найден."""
    pass


class EmailAlreadyVerifiedError(AuthException):
    """Ошибка email уже верифицирован."""
    pass


class UserAlreadyExistsError(AuthException):
    """Ошибка пользователь уже существует."""
    pass


class TokenNotFoundError(AuthException):
    """Ошибка токен не найден."""
    pass

