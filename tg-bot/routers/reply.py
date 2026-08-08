"""Direct reply to discussion comments (bypass publish queue)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reply"])

_bot_service = None


def set_bot_service(service: Any) -> None:
    global _bot_service
    _bot_service = service


class ReplyRequest(BaseModel):
    user_id: int
    chat_id: str
    reply_to_msg_id: int = Field(..., ge=1)
    text: str = Field(..., min_length=1, max_length=4096)


@router.post("/reply")
async def reply_in_chat(body: ReplyRequest) -> dict[str, Any]:
    """Send a Telethon reply_to message in a discussion chat."""
    if not _bot_service or not _bot_service.client_manager:
        raise HTTPException(status_code=503, detail="Bot service not ready")
    client = _bot_service.client_manager.get_client(body.user_id)
    if not client:
        raise HTTPException(status_code=404, detail="Telegram client not connected for user")
    try:
        chat: Any = body.chat_id
        if body.chat_id.lstrip("-").isdigit():
            chat = int(body.chat_id)
        msg = await client.send_message(
            chat,
            body.text,
            reply_to=body.reply_to_msg_id,
        )
        return {
            "ok": True,
            "message_id": getattr(msg, "id", None),
            "chat_id": str(body.chat_id),
            "reply_to": body.reply_to_msg_id,
        }
    except Exception as exc:
        logger.error("reply failed user=%s chat=%s: %s", body.user_id, body.chat_id, exc)
        raise HTTPException(status_code=502, detail=str(exc)[:300]) from exc
