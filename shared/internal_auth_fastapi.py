"""FastAPI dependency helpers for X-Internal-Token."""

from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, status

from shared.internal_auth import INTERNAL_TOKEN_HEADER, get_internal_api_token, verify_internal_token


async def require_internal_token(
    x_internal_token: Optional[str] = Header(None, alias=INTERNAL_TOKEN_HEADER),
) -> None:
    """Reject request unless X-Internal-Token matches INTERNAL_API_TOKEN."""
    ok, reason = verify_internal_token(x_internal_token, get_internal_api_token())
    if ok:
        return
    if reason == "not_configured":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="INTERNAL_API_TOKEN is not configured",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing internal token",
    )
