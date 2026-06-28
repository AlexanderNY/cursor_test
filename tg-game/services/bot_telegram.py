"""Проверка токена Telegram-бота через Bot API."""

from __future__ import annotations

from typing import Any

import httpx


async def fetch_bot_info(token: str) -> dict[str, Any]:
    clean_token = (token or "").strip()
    if not clean_token:
        raise ValueError("Bot token is required")

    url = f"https://api.telegram.org/bot{clean_token}/getMe"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    if not payload.get("ok"):
        description = payload.get("description") or "Invalid bot token"
        raise ValueError(description)

    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("Unexpected Telegram API response")

    return result


def mask_bot_token(token: str) -> str:
    clean = (token or "").strip()
    if len(clean) <= 8:
        return "****"
    return f"{clean[:4]}...{clean[-4:]}"
