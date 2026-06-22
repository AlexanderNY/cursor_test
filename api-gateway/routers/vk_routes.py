from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/vk", tags=["VKontakte"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на core сервис.
    
    Args:
        target_path: Путь на core сервисе
        request: FastAPI Request объект
    
    Returns:
        Response от core сервиса
    """
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request
    )


@router.get("/profile")
async def get_vk_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает профиль VKontakte из core сервиса.
    
    GET /vk/profile -> GET /vk/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/vk/profile", request)


@router.post("/profile")
async def save_vk_profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Сохраняет профиль VKontakte в core сервисе.
    
    POST /vk/profile -> POST /vk/profile на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/vk/profile", request)


@router.get("/profiles")
async def get_all_vk_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает все профили VKontakte из core сервиса.
    
    GET /vk/profiles -> GET /vk/profiles на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/vk/profiles", request)


@router.get("/posts")
async def get_vk_posts(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает посты VKontakte пользователя из core (vk_posts).
    
    GET /vk/posts -> GET /vk/posts на core сервисе
    """
    return await forward_to_core("/vk/posts", request)


@router.get("/post/{post_id}")
async def get_vk_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Получает один пост VKontakte по id."""
    return await forward_to_core(f"/vk/post/{post_id}", request)


@router.put("/post/{post_id}")
async def update_vk_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Обновляет пост VKontakte."""
    return await forward_to_core(f"/vk/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_vk_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Удаляет (помечает deleted) пост VKontakte."""
    return await forward_to_core(f"/vk/post/{post_id}", request)


@router.post("/post")
async def create_vk_post(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Создает пост VKontakte в core сервисе.
    
    POST /vk/post -> POST /vk/post на core сервисе
    Требует JWT аутентификации.
    """
    return await forward_to_core("/vk/post", request)


@router.post("/upload")
async def upload_vk_image(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Загружает изображение для поста VK (multipart). Проксируется в core."""
    return await forward_to_core("/vk/upload", request)


@router.get("/uploads/{filename}")
async def get_vk_upload(
    filename: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Response:
    """Отдаёт загруженный файл из uploads/vk (превью и скачивание)."""
    return await forward_to_core(f"/vk/uploads/{filename}", request)


@router.get("/oauth/url")
async def get_vk_oauth_url(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /vk/oauth/url -> core (JWT)."""
    return await forward_to_core("/vk/oauth/url", request)


@router.get("/oauth/callback")
async def vk_oauth_callback(request: Request) -> Response:
    """OAuth callback VK: проксирование на core (без JWT)."""
    return await forward_to_core("/vk/oauth/callback", request)


@router.get("/oauth/status")
async def vk_oauth_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /vk/oauth/status -> core (JWT)."""
    return await forward_to_core("/vk/oauth/status", request)


@router.get("/subscriptions")
async def vk_subscriptions(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /vk/subscriptions — подписки VK (core, JWT)."""
    return await forward_to_core("/vk/subscriptions", request)
