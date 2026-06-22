from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])


async def forward_to_auth(
    target_path: str,
    request: Request,
    override_method: str | None = None
) -> Response:
    """Перенаправляет запрос на auth сервис.
    
    Args:
        target_path: Путь на auth сервисе
        request: FastAPI Request объект
        override_method: Переопределить HTTP метод (опционально)
    
    Returns:
        Response от auth сервиса
    """
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.AUTH_SERVICE_URL, target_path)
    
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
        override_method=override_method
    )


@router.post("/register")
async def handle_register(request: Request) -> Response:
    """Обрабатывает запрос регистрации пользователя.
    
    POST /auth/register -> POST /register на auth сервисе
    """
    return await forward_to_auth("/register", request)


@router.post("/login")
async def handle_login(request: Request) -> Response:
    """Обрабатывает запрос входа пользователя.
    
    POST /auth/login -> POST /login на auth сервисе
    """
    return await forward_to_auth("/login", request)


@router.post("/refresh")
async def handle_refresh(request: Request) -> Response:
    """Обрабатывает запрос обновления токена.
    
    POST /api/auth/refresh -> POST /refresh на auth сервисе
    """
    return await forward_to_auth("/refresh", request)


@router.post("/logout")
async def handle_logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обрабатывает запрос выхода пользователя.
    
    POST /api/auth/logout -> POST /logout на auth сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_auth("/logout", request)


@router.get("/profile")
async def get_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает профиль текущего пользователя.
    
    GET /api/auth/profile -> GET /profile на auth сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_auth("/profile", request)


@router.post("/profile")
async def update_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обновляет профиль текущего пользователя.
    
    POST /api/auth/profile -> PUT /profile на auth сервисе
    Требует JWT аутентификации.
    Внимание: метод меняется с POST на PUT!
    """
    return await forward_to_auth("/profile", request, override_method="PUT")


@router.post("/verify")
async def handle_verify(request: Request) -> Response:
    """Обрабатывает верификацию email.
    
    POST /api/auth/verify -> POST /verify-token на auth сервисе
    """
    return await forward_to_auth("/verify-token", request)


@router.post("/reset-password")
async def handle_reset_password(request: Request) -> Response:
    """Обрабатывает сброс пароля.
    
    POST /api/auth/reset-password -> POST /reset-password на auth сервисе
    """
    return await forward_to_auth("/reset-password", request)


@router.post("/reset-password/confirm")
async def handle_reset_password_confirm(request: Request) -> Response:
    """Обрабатывает подтверждение сброса пароля.
    
    POST /api/auth/reset-password/confirm -> POST /reset-password/confirm на auth сервисе
    """
    return await forward_to_auth("/reset-password/confirm", request)


@router.post("/all-logout")
async def handle_all_logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обрабатывает выход со всех устройств.
    
    POST /api/auth/all-logout -> POST /all_logout на auth сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_auth("/all_logout", request)


@router.get("/users")
async def get_users(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает список всех пользователей (только для администраторов).

    GET /api/auth/users -> GET /users на auth сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_auth("/users", request)


@router.get("/users/export")
async def export_users_csv(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Экспорт пользователей CSV (админ)."""
    return await forward_to_auth("/users/export", request)


@router.patch("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обновляет роль и/или тариф пользователя (только для администраторов).

    PATCH /api/auth/users/{user_id} -> PATCH /users/{user_id} на auth сервисе
    Требует JWT аутентификации и роли admin.
    """
    return await forward_to_auth(f"/users/{user_id}", request)


@router.get("/users/{user_id}/role-tariff-history")
async def get_role_tariff_history(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """История изменений роли и тарифа пользователя.

    GET /api/auth/users/{user_id}/role-tariff-history -> GET /users/{user_id}/role-tariff-history на auth сервисе
    Админ — любой user_id, иначе только свой.
    """
    return await forward_to_auth(f"/users/{user_id}/role-tariff-history", request)


@router.get("/admin/audit-log")
async def admin_audit_log(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Журнал действий администраторов."""
    return await forward_to_auth("/admin/audit-log", request)


@router.get("/billing/plans")
async def billing_plans(request: Request) -> Response:
    """Матрица тарифов (публично)."""
    return await forward_to_auth("/billing/plans", request)


@router.get("/billing/me")
async def billing_me(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Текущий план и подписка."""
    return await forward_to_auth("/billing/me", request)


@router.post("/billing/customer-portal")
async def billing_customer_portal(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Stripe Customer Portal."""
    return await forward_to_auth("/billing/customer-portal", request)


@router.get("/billing/events")
async def billing_events(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """События биллинга пользователя."""
    return await forward_to_auth("/billing/events", request)


@router.post("/billing/webhooks/stripe")
async def stripe_webhook(request: Request) -> Response:
    """Stripe webhook (без JWT)."""
    return await forward_to_auth("/billing/webhooks/stripe", request)


@router.api_route("/groups/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
async def groups_proxy(
    request: Request,
    path: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Проксирование запросов к группам на auth сервис.

    GET/POST /api/auth/groups, /api/auth/groups/my, /api/auth/groups/{id}/members и т.д.
    Требует JWT аутентификации.
    """
    target_path = f"/groups/{path}" if path.strip() else "/groups"
    return await forward_to_auth(target_path, request)


