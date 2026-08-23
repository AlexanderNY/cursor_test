"""Platform authorization checks for TG/VK before channel/post operations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import httpx

from config import settings
from database import get_db_connection, release_db_connection
from services.profile_service import profile_service
from services.system_settings_service import system_settings_service

logger = logging.getLogger(__name__)

VK_API_VERSION = "5.199"
VK_API_BASE = "https://api.vk.com/method"
SETUP_URLS = {"tg": "/telegram", "vk": "/vkontakte"}


class PlatformAction(str, Enum):
    COLLECT = "collect"
    PUBLISH_TEXT = "publish_text"
    PUBLISH_MEDIA = "publish_media"
    ALERT = "alert"


class PlatformAuthError(Exception):
    def __init__(
        self,
        network: str,
        action: str,
        message: str,
        setup_url: Optional[str] = None,
    ) -> None:
        self.network = network
        self.action = action
        self.message = message
        self.setup_url = setup_url or SETUP_URLS.get(network, "/profile")
        super().__init__(message)


from exceptions import ChannelAccessError


def platform_auth_http_detail(exc: PlatformAuthError) -> dict[str, Any]:
    return {
        "message": exc.message,
        "code": "platform_auth_required",
        "network": exc.network,
        "action": exc.action,
        "setup_url": exc.setup_url,
    }


def match_external_id(needle: str, haystack: Any) -> bool:
    n = str(needle or "").strip()
    h = str(haystack or "").strip()
    if not n or not h:
        return False
    if n == h or n.lstrip("-") == h.lstrip("-"):
        return True
    try:
        return int(n) == int(h)
    except (TypeError, ValueError):
        return False


async def _vk_api_get(method: str, params: dict[str, Any]) -> Any:
    url = f"{VK_API_BASE}/{method}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, params={**params, "v": VK_API_VERSION})
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(err.get("error_msg") or str(err))
        return data.get("response")


class PlatformAuthService:
    async def get_tg_status(self, user_id: int) -> dict[str, Any]:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT auth_state, auth_phone_number FROM tg_profiles WHERE user_id = %s",
                    (user_id,),
                )
                row = await cur.fetchone()
        finally:
            await release_db_connection(conn)

        if not row:
            return {
                "connected": False,
                "state": "missing",
                "message": "Telegram profile not configured",
                "can_collect": False,
                "can_publish_text": False,
                "can_publish_media": False,
                "can_alert": False,
                "setup_url": SETUP_URLS["tg"],
            }

        auth_state = (row[0] or "missing").strip()
        client_active = await self._tg_client_active(user_id)
        connected = auth_state == "authorized" and client_active
        pending = auth_state in ("pending_code", "pending_password")

        return {
            "connected": connected,
            "state": auth_state,
            "client_active": client_active,
            "pending": pending,
            "message": self._tg_message(auth_state, client_active),
            "can_collect": connected,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "can_alert": connected,
            "setup_url": SETUP_URLS["tg"],
        }

    async def get_vk_status(self, user_id: int) -> dict[str, Any]:
        raw = await profile_service.get_vk_profile_tokens_raw(user_id)
        if not raw:
            return {
                "connected": False,
                "state": "missing",
                "message": "VK profile not configured",
                "can_collect": False,
                "can_publish_text": False,
                "can_publish_media": False,
                "setup_url": SETUP_URLS["vk"],
            }

        user_tok = (raw.get("user_access_token") or "").strip()
        comm_tok = (raw.get("access_token") or "").strip()
        has_user = bool(user_tok)
        has_comm = bool(comm_tok)
        connected = has_user or has_comm

        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "vk_user_oauth": has_user,
            "community_token": has_comm,
            "message": (
                "VK connected"
                if connected
                else "Connect VK OAuth or add a community token"
            ),
            "can_collect": has_comm,
            "can_publish_text": has_comm or has_user,
            "can_publish_media": has_user,
            "setup_url": SETUP_URLS["vk"],
        }

    async def get_all_platform_status(self, user_id: int) -> dict[str, Any]:
        tg = await self.get_tg_status(user_id)
        vk = await self.get_vk_status(user_id)
        return {"tg": tg, "vk": vk}

    async def require_platform(
        self,
        user_id: int,
        network: str,
        action: PlatformAction,
    ) -> None:
        network = network.lower()
        if network == "tg":
            status = await self.get_tg_status(user_id)
        elif network == "vk":
            status = await self.get_vk_status(user_id)
        else:
            return

        cap_key = {
            PlatformAction.COLLECT: "can_collect",
            PlatformAction.PUBLISH_TEXT: "can_publish_text",
            PlatformAction.PUBLISH_MEDIA: "can_publish_media",
            PlatformAction.ALERT: "can_alert",
        }.get(action, "can_publish_text")

        if status.get(cap_key):
            return

        label = {
            PlatformAction.COLLECT: "collect",
            PlatformAction.PUBLISH_TEXT: "publish",
            PlatformAction.PUBLISH_MEDIA: "publish with media",
            PlatformAction.ALERT: "send alerts",
        }.get(action, "use platform")

        raise PlatformAuthError(
            network,
            action.value,
            f"{network.upper()} not connected — cannot {label}",
            status.get("setup_url"),
        )

    async def require_targets_auth(
        self,
        user_id: int,
        targets: list[dict],
        *,
        has_media: bool = False,
    ) -> None:
        networks = {str(t.get("network") or "").lower() for t in targets if t.get("network")}
        for net in networks:
            if net == "tg":
                await self.require_platform(user_id, "tg", PlatformAction.PUBLISH_TEXT)
            elif net == "vk":
                action = (
                    PlatformAction.PUBLISH_MEDIA
                    if has_media
                    else PlatformAction.PUBLISH_TEXT
                )
                await self.require_platform(user_id, "vk", action)

    async def fetch_tg_channel_ids(self, user_id: int) -> Optional[list[str]]:
        base = (settings.TG_BOT_SERVICE_URL or "").rstrip("/")
        if not base:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{base}/tg/channels/{user_id}")
                if resp.status_code >= 400:
                    return None
                items = resp.json()
                if not isinstance(items, list):
                    return None
                return [str(item.get("id")) for item in items if item.get("id") is not None]
        except Exception as exc:
            logger.debug("fetch_tg_channel_ids failed user=%s: %s", user_id, exc)
            return None

    async def probe_channel_access(
        self,
        user_id: int,
        network: str,
        external_id: str,
        role: str,
        *,
        strict: bool = False,
    ) -> dict[str, Any]:
        """Probe channel access.

        By default soft: always returns a status dict (channels can be created freely).
        With strict=True (e.g. enabling publish): raises ChannelAccessError if not owned/accessible.
        """
        network = network.lower()
        role = role.lower()
        ext = str(external_id or "").strip()
        now = datetime.utcnow()

        if role == "competitor":
            return {
                "auth_status": "not_required",
                "auth_error": None,
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        if network == "tg":
            result = await self._probe_tg_channel(user_id, ext, now)
        elif network == "vk":
            result = await self._probe_vk_channel(user_id, ext, now)
        else:
            result = {
                "auth_status": "invalid",
                "auth_error": f"Unsupported network {network}",
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        if strict and role == "own" and result.get("auth_status") != "connected":
            raise ChannelAccessError(
                result.get("auth_error")
                or "Channel ownership not confirmed — connect platform and recheck"
            )
        return result

    async def _probe_tg_channel(
        self, user_id: int, external_id: str, now: datetime
    ) -> dict[str, Any]:
        tg = await self.get_tg_status(user_id)
        if not tg.get("connected"):
            state = "pending" if tg.get("pending") else "missing"
            return {
                "auth_status": state,
                "auth_error": tg.get("message"),
                "auth_capabilities": {
                    "can_collect": False,
                    "can_publish_text": False,
                    "can_alert": False,
                },
                "auth_checked_at": now,
            }

        channel_ids = await self.fetch_tg_channel_ids(user_id)
        accessible = False
        if channel_ids:
            accessible = any(match_external_id(external_id, cid) for cid in channel_ids)

        caps = {
            "can_collect": bool(accessible and tg.get("can_collect")),
            "can_publish_text": bool(accessible and tg.get("can_publish_text")),
            "can_alert": bool(accessible and tg.get("can_alert")),
        }

        if accessible:
            return {
                "auth_status": "connected",
                "auth_error": None,
                "auth_capabilities": caps,
                "auth_checked_at": now,
            }

        return {
            "auth_status": "invalid",
            "auth_error": f"Channel {external_id} not found in your Telegram dialogs",
            "auth_capabilities": caps,
            "auth_checked_at": now,
        }

    async def _probe_vk_channel(
        self, user_id: int, external_id: str, now: datetime
    ) -> dict[str, Any]:
        vk = await self.get_vk_status(user_id)
        raw = await profile_service.get_vk_profile_tokens_raw(user_id)
        ext = external_id.lstrip("-")
        try:
            group_id = int(ext)
        except (TypeError, ValueError):
            return {
                "auth_status": "invalid",
                "auth_error": "Invalid VK group id",
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        if not vk.get("connected") or not raw:
            return {
                "auth_status": "missing" if not vk.get("connected") else "invalid",
                "auth_error": vk.get("message"),
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        accessible = False
        token = (raw.get("user_access_token") or raw.get("access_token") or "").strip()
        if token:
            try:
                items = await _vk_api_get(
                    "groups.getById",
                    {
                        "group_ids": str(group_id),
                        "access_token": token,
                        "fields": "members_count",
                    },
                )
                accessible = bool(items)
            except Exception as exc:
                logger.debug("VK groups.getById failed: %s", exc)

        caps = {
            "can_collect": bool(accessible and vk.get("can_collect")),
            "can_publish_text": bool(accessible and vk.get("can_publish_text")),
            "can_publish_media": bool(accessible and vk.get("can_publish_media")),
        }

        if accessible:
            return {
                "auth_status": "connected",
                "auth_error": None,
                "auth_capabilities": caps,
                "auth_checked_at": now,
            }

        return {
            "auth_status": "invalid",
            "auth_error": f"VK group {group_id} not accessible with current tokens",
            "auth_capabilities": caps,
            "auth_checked_at": now,
        }

    async def persist_channel_auth(self, channel_id: int, probe: dict[str, Any]) -> None:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_brand_channels
                    SET auth_status = %s,
                        auth_error = %s,
                        auth_checked_at = %s,
                        auth_capabilities = %s::jsonb
                    WHERE id = %s
                    """,
                    (
                        probe.get("auth_status", "unknown"),
                        probe.get("auth_error"),
                        probe.get("auth_checked_at") or datetime.utcnow(),
                        json.dumps(probe.get("auth_capabilities") or {}, ensure_ascii=False),
                        channel_id,
                    ),
                )
        finally:
            await release_db_connection(conn)

    async def recheck_channel_auth(self, user_id: int, channel_id: int) -> dict[str, Any]:
        from services.smm_service import smm_service

        ch = await smm_service.get_channel(user_id, channel_id)
        if not ch:
            raise ValueError("Channel not found")

        probe = await self.probe_channel_access(
            user_id,
            ch["network"],
            ch["external_id"],
            ch.get("role") or "own",
        )
        await self.persist_channel_auth(channel_id, probe)
        ch.update(
            {
                "auth_status": probe["auth_status"],
                "auth_error": probe.get("auth_error"),
                "auth_checked_at": (
                    probe["auth_checked_at"].isoformat()
                    if probe.get("auth_checked_at")
                    else None
                ),
                "auth_capabilities": probe.get("auth_capabilities") or {},
            }
        )
        return ch

    async def recheck_user_platform_channels(self, user_id: int) -> dict[str, Any]:
        from services.smm_service import smm_service

        channels = await smm_service.list_all_channels(user_id)
        updated = 0
        errors: list[str] = []
        for ch in channels:
            if ch.get("role") == "competitor":
                continue
            try:
                probe = await self.probe_channel_access(
                    user_id,
                    ch["network"],
                    ch["external_id"],
                    ch.get("role") or "own",
                    strict=False,
                )
                await self.persist_channel_auth(int(ch["id"]), probe)
                if (
                    ch.get("role") == "own"
                    and probe.get("auth_status") != "connected"
                    and ch.get("publish_enabled")
                ):
                    conn = await get_db_connection()
                    try:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """
                                UPDATE smm_brand_channels
                                SET publish_enabled = FALSE
                                WHERE id = %s
                                """,
                                (int(ch["id"]),),
                            )
                    finally:
                        await release_db_connection(conn)
                updated += 1
            except ChannelAccessError as exc:
                probe = {
                    "auth_status": "invalid",
                    "auth_error": str(exc),
                    "auth_capabilities": {},
                    "auth_checked_at": datetime.utcnow(),
                }
                await self.persist_channel_auth(int(ch["id"]), probe)
                errors.append(str(exc))
                updated += 1
            except Exception as exc:
                errors.append(f"channel {ch.get('id')}: {exc}")
        return {"updated": updated, "errors": errors}

    async def recheck_stale_channels(self, max_age_hours: int = 24) -> dict[str, Any]:
        since = datetime.utcnow() - timedelta(hours=max_age_hours)
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id, b.user_id
                    FROM smm_brand_channels c
                    JOIN smm_brands b ON b.id = c.brand_id
                    WHERE c.role IN ('own', 'source')
                      AND c.auth_status IN ('connected', 'unknown', 'invalid', 'pending', 'missing')
                      AND (c.auth_checked_at IS NULL OR c.auth_checked_at < %s)
                    LIMIT 200
                    """,
                    (since,),
                )
                rows = await cur.fetchall()
        finally:
            await release_db_connection(conn)

        users = sorted({int(r[1]) for r in rows})
        total = 0
        for uid in users:
            result = await self.recheck_user_platform_channels(uid)
            total += int(result.get("updated") or 0)
        return {"users": len(users), "channels_updated": total}

    async def validate_channel_update(
        self,
        user_id: int,
        channel: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Publish requires ownership confirmation; collect/alert only need platform session."""
        net = channel.get("network", "tg")

        if updates.get("publish_enabled") is True:
            await self.require_platform(user_id, net, PlatformAction.PUBLISH_TEXT)
            probe = await self.probe_channel_access(
                user_id,
                net,
                channel.get("external_id") or "",
                channel.get("role") or "own",
                strict=True,
            )
            await self.persist_channel_auth(int(channel["id"]), probe)
            if probe.get("auth_status") != "connected":
                raise ValueError(
                    "Cannot enable publish: confirm channel ownership first "
                    "(Connect platform → Recheck)."
                )

        if updates.get("collect_enabled") is True and net == "tg":
            await self.require_platform(user_id, "tg", PlatformAction.COLLECT)

        if updates.get("alert_enabled") is True and net == "tg":
            await self.require_platform(user_id, "tg", PlatformAction.ALERT)

    async def get_onboarding_state(self, user_id: int) -> dict[str, Any]:
        from services.smm_service import smm_service

        platforms = await self.get_all_platform_status(user_id)
        brands = await smm_service.list_brands(user_id)
        channels = await smm_service.list_all_channels(user_id)
        own_channels = [c for c in channels if c.get("role") == "own"]
        own_connected = [c for c in own_channels if c.get("auth_status") == "connected"]
        prefs = await system_settings_service.get_value(f"smm_onboarding_{user_id}", {})
        skipped = bool(isinstance(prefs, dict) and prefs.get("skipped"))

        tg_ready = bool(platforms["tg"].get("connected"))
        vk_ready = bool(platforms["vk"].get("connected"))
        has_brand = len(brands) > 0
        has_own_channel = len(own_channels) > 0
        # Channel can be added without ownership; publish still needs connected.
        completed = skipped or has_own_channel

        step = 1
        if tg_ready or vk_ready:
            step = 2
        if has_brand:
            step = 3
        if has_own_channel:
            step = 4
        if own_connected:
            step = 5

        return {
            "step": step,
            "total_steps": 5,
            "tg_ready": tg_ready,
            "vk_ready": vk_ready,
            "has_brand": has_brand,
            "has_own_channel": has_own_channel,
            "has_connected_own_channel": bool(own_connected),
            "skipped": skipped,
            "completed": completed,
            "platforms": platforms,
        }

    async def set_onboarding_skipped(self, user_id: int, skipped: bool = True) -> dict[str, Any]:
        value = {
            "skipped": skipped,
            "updated_at": datetime.utcnow().isoformat(),
        }
        await system_settings_service.set_value(f"smm_onboarding_{user_id}", value)
        return await self.get_onboarding_state(user_id)

    async def _tg_client_active(self, user_id: int) -> bool:
        base = (settings.TG_BOT_SERVICE_URL or "").rstrip("/")
        if not base:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base}/tg/auth/status/{user_id}")
                if resp.status_code >= 400:
                    return False
                data = resp.json()
                return (data.get("auth_state") == "authorized")
        except Exception:
            return False

    @staticmethod
    def _tg_message(auth_state: str, client_active: bool) -> str:
        if auth_state == "authorized" and client_active:
            return "Telegram connected"
        if auth_state == "authorized" and not client_active:
            return "Telegram authorized in DB but bot client inactive — reload tg-bot"
        if auth_state == "pending_password":
            return "Enter Telegram 2FA password"
        if auth_state == "pending_code":
            return "Enter Telegram confirmation code"
        if auth_state == "failed":
            return "Telegram authorization failed"
        return "Configure Telegram API credentials and authorize"


platform_auth_service = PlatformAuthService()
