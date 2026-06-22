"""Маршруты API Gateway для Instagram (проксирование на Core)."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/instagram", tags=["Instagram"])


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
async def get_instagram_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /instagram/profile -> Core."""
    return await forward_to_core("/instagram/profile", request)


@router.post("/profile")
async def save_instagram_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram/profile -> Core."""
    return await forward_to_core("/instagram/profile", request)


@router.get("/profiles")
async def get_all_instagram_profiles(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /instagram/profiles -> Core."""
    return await forward_to_core("/instagram/profiles", request)


@router.get("/posts")
async def get_instagram_posts(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /instagram/posts -> Core."""
    return await forward_to_core("/instagram/posts", request)


@router.get("/post/{post_id}")
async def get_instagram_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """GET /instagram/post/{post_id} -> Core."""
    return await forward_to_core(f"/instagram/post/{post_id}", request)


@router.put("/post/{post_id}")
async def update_instagram_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """PUT /instagram/post/{post_id} -> Core."""
    return await forward_to_core(f"/instagram/post/{post_id}", request)


@router.delete("/post/{post_id}")
async def delete_instagram_post(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """DELETE /instagram/post/{post_id} -> Core."""
    return await forward_to_core(f"/instagram/post/{post_id}", request)


@router.post("/post")
async def create_instagram_post(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """POST /instagram/post -> Core."""
    return await forward_to_core("/instagram/post", request)
