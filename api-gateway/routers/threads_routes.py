"""Проксирование запросов к Core для Threads."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/threads", tags=["Threads"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    """Перенаправляет запрос на core сервис."""
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )


@router.get("/profile")
async def get_threads_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /threads/profile -> core."""
    return await forward_to_core("/threads/profile", request)


@router.post("/profile")
async def save_threads_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /threads/profile -> core."""
    return await forward_to_core("/threads/profile", request)


@router.get("/profiles")
async def get_all_threads_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /threads/profiles -> core."""
    return await forward_to_core("/threads/profiles", request)


@router.post("/post")
async def create_threads_post(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /threads/post -> core."""
    return await forward_to_core("/threads/post", request)


@router.get("/posts")
async def get_threads_posts(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /threads/posts -> core."""
    return await forward_to_core("/threads/posts", request)


@router.get("/post/{post_id}")
async def get_threads_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /threads/post/{post_id} -> core."""
    return await forward_to_core(f"/threads/post/{post_id}", request)


@router.put("/post/{post_id}")
async def update_threads_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """PUT /threads/post/{post_id} -> core."""
    return await forward_to_core(f"/threads/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_threads_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """DELETE /threads/post/{post_id} -> core."""
    return await forward_to_core(f"/threads/post/{post_id}", request)


@router.get("/oauth/callback")
async def threads_oauth_callback(request: Request) -> Response:
    """OAuth callback от Meta: проксирование на core (без JWT)."""
    return await forward_to_core("/threads/oauth/callback", request)
