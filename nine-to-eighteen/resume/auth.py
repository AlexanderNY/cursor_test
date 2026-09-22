"""JWT site_access (aud=9to18) — тот же секрет, что у site-api."""
from __future__ import annotations

from typing import Any, Optional

import jwt
from fastapi import HTTPException

from config import settings
from database import get_db_connection, release_db_connection

SITE_AUD = "9to18"
ALGORITHM = "HS256"


def _secret() -> str:
    secret = (settings.JWT_SECRET_KEY or "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET_KEY is not configured")
    return secret


def bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def decode_site_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[settings.JWT_ALGORITHM or ALGORITHM],
            audience=SITE_AUD,
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if payload.get("type") != "site_access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


async def require_user(authorization: Optional[str]) -> dict[str, Any]:
    token = bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = decode_site_token(token)
    user_id = int(payload["user_id"])
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT username, site_role, is_active, email
                FROM site_users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
    finally:
        await release_db_connection(conn)
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    if not bool(row[2]):
        raise HTTPException(status_code=403, detail="Account disabled")
    return {
        "user_id": user_id,
        "username": str(row[0] or ""),
        "site_role": str(row[1] or "user"),
        "email": str(row[3] or ""),
    }
