"""Чтение/запись глобальных runtime-настроек (system_settings)."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from database import get_db_connection, release_db_connection

AI_ENABLED_KEY = "ai_enabled"


class SystemSettingsService:
    async def get_value(self, key: str, default: Any = None) -> Any:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT value FROM system_settings WHERE key = %s",
                    (key,),
                )
                row = await cur.fetchone()
                if not row:
                    return default
                value = row[0]
                if isinstance(value, (dict, list, bool, int, float)) or value is None:
                    return value
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                return value
        finally:
            await release_db_connection(conn)

    async def set_value(self, key: str, value: Any) -> Any:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO system_settings (key, value, updated_at)
                    VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING value
                    """,
                    (key, json.dumps(value)),
                )
                row = await cur.fetchone()
                return row[0] if row else value
        finally:
            await release_db_connection(conn)

    @staticmethod
    def is_env_ai_enabled() -> bool:
        return os.getenv("AI_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")

    async def is_ai_enabled(self) -> bool:
        value = await self.get_value(AI_ENABLED_KEY, True)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    async def set_ai_enabled(self, enabled: bool) -> bool:
        await self.set_value(AI_ENABLED_KEY, bool(enabled))
        return bool(enabled)

    async def get_ai_settings(self) -> dict[str, Any]:
        enabled = await self.is_ai_enabled()
        env_enabled = self.is_env_ai_enabled()
        available = False
        circuit_open = False
        status = "disabled"
        try:
            from shared import ai_client

            snapshot = await ai_client.get_status()
            available = bool(snapshot.get("available"))
            circuit_open = bool(snapshot.get("circuit_open"))
            status = str(snapshot.get("status") or status)
            # get_status уже учитывает env + DB через is_enabled poll;
            # для admin UI источником правды по DB-флагу остаётся is_ai_enabled().
            if not env_enabled:
                status = "disabled"
            elif not enabled:
                status = "disabled"
        except Exception:
            status = "unavailable" if enabled and env_enabled else "disabled"

        return {
            "enabled": enabled,
            "env_enabled": env_enabled,
            "model": os.getenv("AI_MODEL", "qwen2.5:3b"),
            "service_url": os.getenv("AI_SERVICE_URL", "http://ollama:65535"),
            "available": available,
            "circuit_open": circuit_open,
            "status": status,
        }


system_settings_service = SystemSettingsService()
