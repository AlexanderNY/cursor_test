"""Redis-backed JWT access-token blacklist (shared by auth + gateway).

Key layout:
  jwt:bl:{sha256(token)}  → "1" with TTL until token exp
  jwt:bl:ready            → "1" after auth finishes warm from Postgres

Gateway trusts Redis only when the ready flag is set; otherwise falls back
to auth HTTP /blacklist-check (fail-closed).
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

KEY_PREFIX = "jwt:bl:"
READY_KEY = "jwt:bl:ready"
TOKENS_VALID_AFTER_PREFIX = "user:tokens_valid_after:"


def tokens_valid_after_key(user_id: int) -> str:
    return f"{TOKENS_VALID_AFTER_PREFIX}{int(user_id)}"


def token_blacklist_key(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{KEY_PREFIX}{digest}"


def ttl_seconds_until(expires_at: datetime) -> int:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(1, int((expires_at - now).total_seconds()))


class TokenBlacklistRedis:
    """Thin async wrapper around redis.asyncio for JWT blacklist keys."""

    def __init__(self) -> None:
        self._client: Any = None
        self._url: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    @property
    def connected(self) -> bool:
        return self._client is not None

    async def connect(self, url: str) -> bool:
        self._url = (url or "").strip()
        if not self._url:
            self._client = None
            return False
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
            await client.ping()
            self._client = client
            logger.info("Token blacklist Redis connected")
            return True
        except Exception as exc:
            self._client = None
            logger.warning("Token blacklist Redis unavailable: %s", exc)
            return False

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def mark_ready(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(READY_KEY, "1")
        except Exception as exc:
            logger.warning("Redis mark_ready failed: %s", exc)

    async def is_ready(self) -> Optional[bool]:
        """True/False if Redis answered; None if Redis down."""
        if self._client is None:
            return None
        try:
            return bool(await self._client.exists(READY_KEY))
        except Exception as exc:
            logger.debug("Redis is_ready failed: %s", exc)
            return None

    async def add(self, token: str, expires_at: datetime) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.set(
                token_blacklist_key(token),
                "1",
                ex=ttl_seconds_until(expires_at),
            )
            return True
        except Exception as exc:
            logger.warning("Redis blacklist add failed: %s", exc)
            return False

    async def contains(self, token: str) -> Optional[bool]:
        """True/False if Redis answered; None if Redis down."""
        if self._client is None:
            return None
        try:
            return bool(await self._client.exists(token_blacklist_key(token)))
        except Exception as exc:
            logger.debug("Redis blacklist contains failed: %s", exc)
            return None

    async def warm(self, rows: list[tuple[str, datetime]]) -> int:
        """Load active Postgres blacklist rows into Redis. Returns written count."""
        if self._client is None:
            return 0
        written = 0
        try:
            pipe = self._client.pipeline(transaction=False)
            for token, expires_at in rows:
                if not token:
                    continue
                ttl = ttl_seconds_until(expires_at)
                pipe.set(token_blacklist_key(token), "1", ex=ttl)
                written += 1
            if written:
                await pipe.execute()
            await self.mark_ready()
            logger.info("Token blacklist Redis warmed with %s keys", written)
            return written
        except Exception as exc:
            logger.warning("Redis blacklist warm failed: %s", exc)
            return 0

    async def set_tokens_valid_after(self, user_id: int, epoch_seconds: int) -> bool:
        """Invalidate access JWTs with iat < epoch_seconds for this user."""
        if self._client is None:
            return False
        try:
            # Keep until well past max access TTL (30m default → 7d safety).
            await self._client.set(
                tokens_valid_after_key(user_id),
                str(int(epoch_seconds)),
                ex=7 * 24 * 3600,
            )
            return True
        except Exception as exc:
            logger.warning("Redis set_tokens_valid_after failed: %s", exc)
            return False

    async def get_tokens_valid_after(self, user_id: int) -> Optional[int]:
        """Epoch seconds; None if unset or Redis down."""
        if self._client is None:
            return None
        try:
            raw = await self._client.get(tokens_valid_after_key(user_id))
            if raw is None:
                return None
            return int(raw)
        except Exception as exc:
            logger.debug("Redis get_tokens_valid_after failed: %s", exc)
            return None


# Process-local singleton (auth and gateway each have their own process).
token_blacklist_redis = TokenBlacklistRedis()
