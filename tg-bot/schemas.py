"""Схемы данных для API."""

from typing import Optional
from pydantic import BaseModel


class PhoneCodeRequest(BaseModel):
    """Запрос на отправку кода подтверждения."""
    user_id: int
    code: str


class PasswordRequest(BaseModel):
    """Запрос на отправку 2FA пароля."""
    user_id: int
    password: str


class AuthStatusResponse(BaseModel):
    """Ответ со статусом авторизации."""
    user_id: int
    auth_state: str
    message: str


class AuthResponse(BaseModel):
    """Ответ на запрос авторизации."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    requires_password: bool = False


class ChannelItem(BaseModel):
    """Элемент списка канала (id и название)."""
    id: int
    title: str
