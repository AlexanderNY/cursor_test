"""Push collected VK posts into Core SMM inbox."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


async def push_inbox_ingest(
    *,
    user_id: int,
    network: str,
    external_id: str,
    text: str,
    author: Optional[str] = None,
    external_msg_id: Optional[str] = None,
    item_type: str = "post",
) -> None:
    base = (settings.CORE_SERVICE_URL or "").rstrip("/")
    if not base:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base}/internal/smm/inbox/ingest",
                json={
                    "user_id": user_id,
                    "network": network,
                    "external_id": str(external_id),
                    "text": text or "",
                    "author": author,
                    "external_msg_id": str(external_msg_id) if external_msg_id is not None else None,
                    "item_type": item_type,
                },
            )
            if resp.status_code >= 400:
                logger.debug("inbox ingest HTTP %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.debug("inbox ingest failed: %s", exc)
