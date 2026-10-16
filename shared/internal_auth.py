"""Service-to-service auth via X-Internal-Token (Docker network)."""

from __future__ import annotations

import hmac
import os
from typing import Optional

INTERNAL_TOKEN_HEADER = "X-Internal-Token"
INTERNAL_TOKEN_ENV = "INTERNAL_API_TOKEN"


def get_internal_api_token() -> str:
    """Configured internal token from environment (may be empty)."""
    return (os.environ.get(INTERNAL_TOKEN_ENV) or "").strip()


def internal_auth_headers(token: Optional[str] = None) -> dict[str, str]:
    """Headers for outbound service calls. Empty token → no header."""
    value = (token if token is not None else get_internal_api_token()).strip()
    if not value:
        return {}
    return {INTERNAL_TOKEN_HEADER: value}


def verify_internal_token(
    provided: Optional[str],
    expected: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate X-Internal-Token.

    Returns (ok, error_code) where error_code is '' | 'not_configured' | 'invalid'.
    """
    expected_value = (expected if expected is not None else get_internal_api_token()).strip()
    provided_value = (provided or "").strip()
    if not expected_value:
        return False, "not_configured"
    if not provided_value:
        return False, "invalid"
    if not hmac.compare_digest(provided_value, expected_value):
        return False, "invalid"
    return True, ""
