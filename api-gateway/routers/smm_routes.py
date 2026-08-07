"""Gateway proxy for SMM endpoints → Core."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from config import settings
from services.proxy_service import get_proxy_service
from middleware.jwt_validator import get_current_user


router = APIRouter(prefix="/smm", tags=["SMM"])


async def forward_to_core(target_path: str, request: Request) -> Response:
    proxy_service = get_proxy_service()
    target_url = proxy_service.build_target_url(settings.CORE_SERVICE_URL, target_path)
    return await proxy_service.forward_request(
        target_url=target_url,
        method=request.method,
        request=request,
    )


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_smm(
    path: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Proxy all /smm/* to core /smm/*."""
    target = f"/smm/{path}" if path else "/smm"
    # Preserve query string via proxy_service (request includes it)
    return await forward_to_core(target, request)
