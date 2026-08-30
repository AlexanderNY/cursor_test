"""Gateway proxy for 9to18 site contour → Core /site/*."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/site", tags=["Site9to18"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def site_proxy(
    request: Request,
    path: str = "",
    current_user: dict | None = Depends(get_current_user),
) -> Response:
    """Все /site/* проксируются в core; JWT 9to18 проверяет core."""
    target = f"/site/{path}" if path else "/site"
    return await forward_to_core(target, request)
