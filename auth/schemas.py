from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime
from typing import Any, Dict, Optional, Literal, List


class UserRegister(BaseModel):
    """Схема для регистрации пользователя."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Схема для входа пользователя."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Схема ответа с токенами."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Схема запроса на обновление токена."""
    refresh_token: str


class UserGroupSummary(BaseModel):
    """Кратко: одна группа пользователя (может быть несколько)."""
    group_id: int
    group_name: str
    role_in_group: Literal["manager", "author"]


class UserProfile(BaseModel):
    """Схема профиля пользователя."""
    id: Optional[int] = None
    username: str
    email: EmailStr
    role: Literal["guest", "user", "admin", "manager", "author"]
    tariff: str = "free"
    is_email_verified: bool
    is_blocked: bool = False
    created_at: datetime
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    role_in_group: Optional[Literal["manager", "author"]] = None
    groups: Optional[List[UserGroupSummary]] = None
    billing_provider: Optional[str] = None
    billing_customer_id: Optional[str] = None
    billing_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_current_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminAuditLogEntry(BaseModel):
    """Запись журнала действий администратора."""
    id: int
    admin_user_id: int
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Схема для обновления профиля пользователя."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class AdminUserUpdate(BaseModel):
    """Схема для обновления роли и тарифа пользователя (только для администраторов)."""
    role: Optional[Literal["guest", "user", "admin", "manager", "author"]] = None
    tariff: Optional[str] = Field(None, max_length=50)
    is_blocked: Optional[bool] = None


class PasswordResetRequest(BaseModel):
    """Схема запроса на сброс пароля."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Схема подтверждения сброса пароля."""
    token: str
    new_password: str = Field(..., min_length=8)


class TokenVerifyRequest(BaseModel):
    """Схема запроса на валидацию токена."""
    token: str


class TokenVerifyResponse(BaseModel):
    """Схема ответа на валидацию токена."""
    valid: bool
    user_id: Optional[int] = None


class GroupCreate(BaseModel):
    """Схема создания группы (менеджер или admin)."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)


class GroupCreateAdmin(BaseModel):
    """Создание пустой группы администратором (участников добавляют отдельно)."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)


class GroupUpdate(BaseModel):
    """Обновление названия и/или описания группы."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=4000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "GroupUpdate":
        if self.name is None and self.description is None:
            raise ValueError("Укажите name и/или description")
        return self


class GroupMemberResponse(BaseModel):
    """Участник группы в ответе API."""
    user_id: int
    username: str
    email: str
    tariff: str
    role_in_group: Literal["manager", "author"]
    joined_at: datetime

    class Config:
        from_attributes = True


class GroupResponse(BaseModel):
    """Группа в ответе API."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    created_by_user_id: Optional[int] = None
    role_in_group: Optional[Literal["manager", "author"]] = None
    members: Optional[List["GroupMemberResponse"]] = None

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    """Добавление участника по email."""
    email: str = Field(..., min_length=1)
    role_in_group: Literal["manager", "author"] = "author"


def user_profile_from_user_dict(
    user: dict,
    memberships: Optional[list] = None,
) -> UserProfile:
    """Собирает UserProfile из строки users и опционально списка групп."""
    first = memberships[0] if memberships else None
    groups_list: Optional[List[UserGroupSummary]] = None
    if memberships:
        groups_list = [
            UserGroupSummary(
                group_id=m["group_id"],
                group_name=m["group_name"],
                role_in_group=m["role_in_group"],
            )
            for m in memberships
        ]
    return UserProfile(
        id=user.get("id"),
        username=user["username"],
        email=user["email"],
        role=user["role"],
        tariff=user.get("tariff", "free"),
        is_email_verified=user["is_email_verified"],
        is_blocked=bool(user.get("is_blocked", False)),
        created_at=user["created_at"],
        group_id=first["group_id"] if first else None,
        group_name=first["group_name"] if first else None,
        role_in_group=first["role_in_group"] if first else None,
        groups=groups_list,
        billing_provider=user.get("billing_provider"),
        billing_customer_id=user.get("billing_customer_id"),
        billing_subscription_id=user.get("billing_subscription_id"),
        subscription_status=user.get("subscription_status"),
        subscription_current_period_end=user.get("subscription_current_period_end"),
    )


class RoleTariffHistoryEntry(BaseModel):
    """Запись истории изменения роли и тарифа пользователя."""
    id: int
    user_id: int
    changed_at: datetime
    changed_by_user_id: Optional[int] = None
    role_old: Optional[str] = None
    role_new: Optional[str] = None
    tariff_old: Optional[str] = None
    tariff_new: Optional[str] = None

    class Config:
        from_attributes = True

