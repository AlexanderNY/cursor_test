"""Signed OAuth state (HMAC-SHA256), shared by VK-style flows for Threads/X.

Format: ``user_id.exp.nonce.sig`` where sig is hex HMAC of ``user_id.exp.nonce``.
"""

from __future__ import annotations

import hmac
import hashlib
import secrets
import time
from typing import Optional


DEFAULT_OAUTH_STATE_TTL_SEC = 600


def sign_oauth_state(
    user_id: int,
    secret: str,
    *,
    ttl_sec: int = DEFAULT_OAUTH_STATE_TTL_SEC,
) -> str:
    """Build signed state for OAuth redirect."""
    secret_bytes = (secret or "").encode("utf-8")
    if not secret_bytes:
        raise ValueError("OAuth state secret is empty")
    exp = int(time.time()) + int(ttl_sec)
    nonce = secrets.token_hex(8)
    payload = f"{int(user_id)}.{exp}.{nonce}"
    sig = hmac.new(secret_bytes, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_oauth_state(state: str, secret: str) -> Optional[int]:
    """Return user_id if state is valid and not expired; else None."""
    if not state or not secret:
        return None
    parts = state.split(".")
    if len(parts) != 4:
        return None
    user_part, exp_part, nonce, sig = parts
    if not nonce or not sig:
        return None
    try:
        user_id = int(user_part)
        exp = int(exp_part)
    except (TypeError, ValueError):
        return None
    if exp < int(time.time()):
        return None
    payload = f"{user_part}.{exp_part}.{nonce}"
    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return user_id
