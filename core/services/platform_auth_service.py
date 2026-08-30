"""Platform authorization checks for TG/VK/IG/… before channel/post operations."""

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
from services.smm_networks import SETUP_URLS, normalize_network, network_label, setup_url
from services.vk_helpers import (
    extract_vk_screen_name,
    groups_from_get_by_id,
    parse_vk_group_id,
)

logger = logging.getLogger(__name__)

VK_API_VERSION = "5.199"
VK_API_BASE = "https://api.vk.com/method"


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
        self.setup_url = setup_url or SETUP_URLS.get(network, "/channels")
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
        # Real VK community tokens are long; reject obvious placeholders.
        has_comm = bool(comm_tok) and len(comm_tok) >= 20
        connected = has_user or has_comm

        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "vk_user_oauth": has_user,
            "community_token": has_comm,
            "message": (
                "VK connected"
                if connected
                else (
                    "Community token missing or invalid — update in VKontakte → Auth"
                    if comm_tok and len(comm_tok) < 20
                    else "Connect VK OAuth or add a community token"
                )
            ),
            # Чтение чужих/своих стен: user OAuth. Community-токен — для wall.post в свою группу.
            "can_collect": has_user,
            "can_alert": has_user,
            "can_publish_text": has_comm or has_user,
            "can_publish_media": has_user,
            "setup_url": SETUP_URLS["vk"],
        }

    async def get_instagram_status(self, user_id: int) -> dict[str, Any]:
        profile = await profile_service.get_instagram_profile(user_id)
        if not profile:
            return self._missing_status("instagram", "Instagram profile not configured")
        connected = bool(profile.get("has_instagram_session"))
        pending = bool(profile.get("instagram_verification_pending"))
        return {
            "connected": connected,
            "state": "pending" if pending else ("authorized" if connected else "missing"),
            "pending": pending,
            "username": profile.get("username"),
            "message": (
                "Instagram connected"
                if connected
                else (
                    "Instagram verification pending"
                    if pending
                    else "Connect Instagram session"
                )
            ),
            "can_collect": connected,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "setup_url": SETUP_URLS["instagram"],
        }

    async def get_threads_status(self, user_id: int) -> dict[str, Any]:
        profile = await profile_service.get_threads_profile(user_id)
        if not profile:
            return self._missing_status("threads", "Threads profile not configured")
        connected = bool(profile.get("threads_connected") or profile.get("access_token"))
        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "threads_user_id": profile.get("threads_user_id"),
            "message": "Threads connected" if connected else "Connect Threads OAuth",
            "can_collect": connected,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "setup_url": SETUP_URLS["threads"],
        }

    async def get_tw_status(self, user_id: int) -> dict[str, Any]:
        profile = await profile_service.get_tw_profile(user_id)
        if not profile:
            return self._missing_status("tw", "Twitter profile not configured")
        connected = bool(profile.get("twitter_connected"))
        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "username": profile.get("twitter_username"),
            "message": "Twitter connected" if connected else "Connect Twitter OAuth",
            "can_collect": connected,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "setup_url": SETUP_URLS["tw"],
        }

    async def get_dzen_status(self, user_id: int) -> dict[str, Any]:
        profile = await profile_service.get_dzen_profile(user_id)
        if not profile:
            return self._missing_status("dzen", "Дзен profile not configured")
        has_creds = bool(profile.get("yandex_login")) and bool(
            profile.get("yandex_password")
        )
        # Password may be masked as ***; treat login + password/studio as configured
        connected = bool(profile.get("yandex_login")) and (
            has_creds or bool(profile.get("dzen_studio_url"))
        )
        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "username": profile.get("yandex_login"),
            "message": "Дзен connected" if connected else "Connect Яндекс / Дзен Studio",
            "can_collect": connected,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "setup_url": SETUP_URLS["dzen"],
        }

    async def get_wp_status(self, user_id: int) -> dict[str, Any]:
        profile = await profile_service.get_wp_publish_profile(user_id)
        if not profile:
            return self._missing_status("wp", "WordPress profile not configured")
        site = (profile.get("site_url") or "").strip()
        user = (profile.get("username") or "").strip()
        connected = bool(site and user)
        return {
            "connected": connected,
            "state": "authorized" if connected else "missing",
            "username": user or site,
            "site_url": site,
            "message": "WordPress connected" if connected else "Configure WP site + app password",
            "can_collect": False,
            "can_publish_text": connected,
            "can_publish_media": connected,
            "setup_url": SETUP_URLS["wp"],
        }

    @staticmethod
    def _missing_status(network: str, message: str) -> dict[str, Any]:
        return {
            "connected": False,
            "state": "missing",
            "message": message,
            "can_collect": False,
            "can_publish_text": False,
            "can_publish_media": False,
            "can_alert": False,
            "setup_url": SETUP_URLS.get(network, "/channels"),
        }

    async def get_all_platform_status(self, user_id: int) -> dict[str, Any]:
        tg = await self.get_tg_status(user_id)
        vk = await self.get_vk_status(user_id)
        instagram = await self.get_instagram_status(user_id)
        threads = await self.get_threads_status(user_id)
        tw = await self.get_tw_status(user_id)
        dzen = await self.get_dzen_status(user_id)
        wp = await self.get_wp_status(user_id)
        return {
            "tg": tg,
            "vk": vk,
            "instagram": instagram,
            "threads": threads,
            "tw": tw,
            "dzen": dzen,
            "wp": wp,
        }

    async def suggest_profile_external_id(
        self, user_id: int, network: str
    ) -> Optional[str]:
        """Best-effort handle/id from *_profiles for channel bind."""
        network = normalize_network(network)
        if network == "instagram":
            p = await profile_service.get_instagram_profile(user_id)
            return (p or {}).get("username") or None
        if network == "threads":
            p = await profile_service.get_threads_profile(user_id)
            return (p or {}).get("threads_user_id") or (p or {}).get("instagram_handle") or None
        if network == "tw":
            p = await profile_service.get_tw_profile(user_id)
            return (p or {}).get("twitter_username") or (p or {}).get("twitter_rest_id") or None
        if network == "dzen":
            p = await profile_service.get_dzen_profile(user_id)
            return (p or {}).get("yandex_login") or (p or {}).get("dzen_studio_url") or None
        if network == "wp":
            p = await profile_service.get_wp_publish_profile(user_id)
            return (p or {}).get("site_url") or (p or {}).get("username") or None
        if network == "vk":
            raw = await profile_service.get_vk_profile_tokens_raw(user_id)
            group = (raw or {}).get("group_to_post")
            return str(group) if group else None
        return None

    async def require_platform(
        self,
        user_id: int,
        network: str,
        action: PlatformAction,
    ) -> None:
        network = normalize_network(network)
        status_getters = {
            "tg": self.get_tg_status,
            "vk": self.get_vk_status,
            "instagram": self.get_instagram_status,
            "threads": self.get_threads_status,
            "tw": self.get_tw_status,
            "dzen": self.get_dzen_status,
            "wp": self.get_wp_status,
        }
        getter = status_getters.get(network)
        if not getter:
            return
        status = await getter(user_id)

        cap_key = {
            PlatformAction.COLLECT: "can_collect",
            PlatformAction.PUBLISH_TEXT: "can_publish_text",
            PlatformAction.PUBLISH_MEDIA: "can_publish_media",
            PlatformAction.ALERT: "can_alert",
        }.get(action, "can_publish_text")

        if status.get(cap_key) or (
            action in (PlatformAction.PUBLISH_TEXT, PlatformAction.PUBLISH_MEDIA)
            and status.get("connected")
        ):
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
            f"{network_label(network)} not connected — cannot {label}",
            status.get("setup_url"),
        )

    async def require_targets_auth(
        self,
        user_id: int,
        targets: list[dict],
        *,
        has_media: bool = False,
    ) -> None:
        networks = {
            normalize_network(t.get("network"))
            for t in targets
            if t.get("network")
        }
        for net in networks:
            if net == "url":
                continue
            action = (
                PlatformAction.PUBLISH_MEDIA
                if has_media and net == "vk"
                else PlatformAction.PUBLISH_TEXT
            )
            await self.require_platform(user_id, net, action)

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
        network = normalize_network(network)
        role = role.lower()
        ext = str(external_id or "").strip()
        now = datetime.utcnow()

        if role == "competitor" and network != "vk":
            return {
                "auth_status": "not_required",
                "auth_error": None,
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        if network == "url":
            return {
                "auth_status": "not_required",
                "auth_error": None,
                "auth_capabilities": {
                    "can_collect": True,
                    "can_publish_text": False,
                    "can_alert": False,
                },
                "auth_checked_at": now,
            }

        if network == "tg":
            result = await self._probe_tg_channel(user_id, ext, now)
        elif network == "vk":
            result = await self._probe_vk_channel(user_id, ext, now, role=role)
        elif network in ("instagram", "threads", "tw", "dzen", "wp"):
            result = await self._probe_profile_network(user_id, network, ext, now)
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

    async def _probe_profile_network(
        self,
        user_id: int,
        network: str,
        external_id: str,
        now: datetime,
    ) -> dict[str, Any]:
        status_getters = {
            "instagram": self.get_instagram_status,
            "threads": self.get_threads_status,
            "tw": self.get_tw_status,
            "dzen": self.get_dzen_status,
            "wp": self.get_wp_status,
        }
        status = await status_getters[network](user_id)
        if not status.get("connected"):
            return {
                "auth_status": "pending" if status.get("pending") else "missing",
                "auth_error": status.get("message"),
                "auth_capabilities": {
                    "can_collect": False,
                    "can_publish_text": False,
                    "can_alert": False,
                },
                "auth_checked_at": now,
            }

        suggested = await self.suggest_profile_external_id(user_id, network)
        # Own account channels: match handle, or accept any id when profile is connected
        # and external_id was set (publish goes through single account session).
        accessible = True
        if suggested and external_id:
            accessible = match_external_id(external_id, suggested) or (
                external_id.lstrip("@").lower() == str(suggested).lstrip("@").lower()
            )
            # Soft: still allow publish if platform session exists (single-account bots)
            if not accessible and network in ("instagram", "threads", "tw", "dzen", "wp"):
                accessible = True

        caps = {
            "can_collect": bool(accessible and status.get("can_collect")),
            "can_publish_text": bool(accessible and status.get("can_publish_text")),
            "can_publish_media": bool(accessible and status.get("can_publish_media")),
            "can_alert": bool(accessible and status.get("can_alert", False)),
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
            "auth_error": (
                f"{network_label(network)} handle mismatch: "
                f"expected {suggested}, got {external_id}"
            ),
            "auth_capabilities": caps,
            "auth_checked_at": now,
        }

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

    async def _vk_tokens_for_probe(
        self, user_id: int, raw: dict[str, Any], *, prefer_user: bool = True
    ) -> list[str]:
        """Tokens for VK lookups (user OAuth first when reading / resolving screen names)."""
        tokens: list[str] = []
        order = ("user_access_token", "access_token")
        if not prefer_user:
            order = ("access_token", "user_access_token")
        for key in order:
            token = (raw.get(key) or "").strip()
            if token and token not in tokens:
                tokens.append(token)
        try:
            oauth = await profile_service.get_vk_oauth_config_raw(user_id)
            service = ((oauth or {}).get("vk_app_service_key") or "").strip()
            if service and service not in tokens:
                tokens.append(service)
        except Exception as exc:
            logger.debug("VK service key lookup failed user=%s: %s", user_id, exc)
        return tokens

    async def _resolve_vk_group_id(
        self, raw_external_id: str, tokens: list[str]
    ) -> tuple[Optional[int], Optional[str]]:
        """Resolve channel external_id to numeric group id. Returns (id, error)."""
        group_id = parse_vk_group_id(raw_external_id)
        if group_id is not None:
            return group_id, None

        screen = extract_vk_screen_name(raw_external_id)
        if not screen:
            return None, (
                "Invalid VK group id — use numeric id, club123, screen name, or vk.com/… URL"
            )
        if not tokens:
            return None, f"Cannot resolve screen name «{screen}» without a VK token"

        last_err: Optional[str] = None

        # Prefer groups.getById — accepts screen names; works with user/community/service tokens.
        for token in tokens:
            try:
                items = await _vk_api_get(
                    "groups.getById",
                    {
                        "group_id": screen,
                        "access_token": token,
                        "fields": "screen_name",
                    },
                )
                groups = groups_from_get_by_id(items)
                if groups and groups[0].get("id") is not None:
                    return int(groups[0]["id"]), None
                last_err = f"VK community «{screen}» not found"
            except Exception as exc:
                last_err = str(exc)
                logger.debug("VK getById screen=%s failed: %s", screen, exc)

        # Fallback: utils.resolveScreenName (often blocked for community tokens).
        for token in tokens:
            try:
                resolved = await _vk_api_get(
                    "utils.resolveScreenName",
                    {"screen_name": screen, "access_token": token},
                )
            except Exception as exc:
                last_err = str(exc)
                continue
            if not isinstance(resolved, dict) or not resolved:
                last_err = f"«{screen}» not found"
                continue
            if resolved.get("type") not in ("group", "page", "event"):
                last_err = f"«{screen}» is not a VK community (type={resolved.get('type')})"
                continue
            try:
                return int(resolved["object_id"]), None
            except (TypeError, ValueError, KeyError):
                last_err = f"Could not resolve «{screen}»"
        return None, last_err or f"Could not resolve «{screen}»"

    async def _probe_vk_channel(
        self,
        user_id: int,
        external_id: str,
        now: datetime,
        *,
        role: str = "own",
    ) -> dict[str, Any]:
        """Probe VK channel.

        - own: community token for this group (publish) and/or user token (read).
        - source / competitor: user OAuth to resolve and read foreign walls.
        """
        vk = await self.get_vk_status(user_id)
        raw = await profile_service.get_vk_profile_tokens_raw(user_id)
        role_norm = (role or "own").lower()
        is_read_role = role_norm in ("source", "competitor")

        if not vk.get("connected") or not raw:
            return {
                "auth_status": "missing" if not vk.get("connected") else "invalid",
                "auth_error": vk.get("message"),
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        user_tok = (raw.get("user_access_token") or "").strip()
        comm_tok = (raw.get("access_token") or "").strip()

        if is_read_role and not user_tok:
            return {
                "auth_status": "missing",
                "auth_error": (
                    "Для чтения чужих групп нужен пользовательский VK OAuth "
                    "(VKontakte → Авторизация → OAuth user)"
                ),
                "auth_capabilities": {
                    "can_collect": False,
                    "can_publish_text": False,
                    "can_publish_media": False,
                },
                "auth_checked_at": now,
            }

        tokens = await self._vk_tokens_for_probe(
            user_id, raw, prefer_user=is_read_role or bool(user_tok)
        )
        if not tokens:
            return {
                "auth_status": "missing",
                "auth_error": "No VK tokens available",
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        # Resolve screen name preferentially with user token for read roles.
        resolve_tokens = [user_tok] + [t for t in tokens if t != user_tok] if user_tok else tokens
        group_id, resolve_err = await self._resolve_vk_group_id(external_id, resolve_tokens)
        if group_id is None:
            return {
                "auth_status": "invalid",
                "auth_error": resolve_err or "Invalid VK group id",
                "auth_capabilities": {},
                "auth_checked_at": now,
            }

        configured_id = parse_vk_group_id(raw.get("group_to_post"))
        is_configured_own = (
            configured_id is not None
            and configured_id == group_id
            and bool(comm_tok)
        )
        last_err: Optional[str] = None
        # Community tokens that are placeholders / revoked must not look "connected".
        if is_configured_own:
            if len(comm_tok) < 20:
                is_configured_own = False
                last_err = (
                    "Community access_token слишком короткий или повреждён — "
                    "обновите токен сообщества (VKontakte → Авторизация)"
                )
            else:
                try:
                    await _vk_api_get(
                        "groups.getById",
                        {
                            "group_id": str(group_id),
                            "access_token": comm_tok,
                            "fields": "screen_name",
                        },
                    )
                except Exception as exc:
                    is_configured_own = False
                    last_err = f"Community token invalid: {exc}"
                    logger.info(
                        "VK community token probe failed user=%s group=%s: %s",
                        user_id,
                        group_id,
                        exc,
                    )

        readable = False
        # Reading: prefer user token (foreign walls). Fallback: service / community.
        read_tokens = [user_tok] if user_tok else []
        if not is_read_role:
            for t in tokens:
                if t and t not in read_tokens:
                    read_tokens.append(t)
        elif not read_tokens:
            read_tokens = tokens

        for token in read_tokens:
            try:
                items = await _vk_api_get(
                    "groups.getById",
                    {
                        "group_id": str(group_id),
                        "access_token": token,
                        "fields": "members_count,screen_name",
                    },
                )
                if groups_from_get_by_id(items):
                    readable = True
                    break
                last_err = f"VK group {group_id} not found"
            except Exception as exc:
                last_err = str(exc)
                logger.debug("VK groups.getById failed group=%s: %s", group_id, exc)

        if is_read_role:
            caps = {
                "can_collect": bool(readable and user_tok),
                "can_alert": bool(readable and user_tok),
                "can_publish_text": False,
                "can_publish_media": False,
            }
            if readable:
                return {
                    "auth_status": "connected",
                    "auth_error": None,
                    "auth_capabilities": caps,
                    "auth_checked_at": now,
                    "resolved_external_id": str(group_id),
                }
            return {
                "auth_status": "invalid",
                "auth_error": last_err
                or f"VK group {group_id} not readable with user OAuth",
                "auth_capabilities": caps,
                "auth_checked_at": now,
                "resolved_external_id": str(group_id),
            }

        # own: publish via community for this group; collect/alert via user if readable
        accessible = is_configured_own or readable
        caps = {
            "can_collect": bool(readable and user_tok),
            "can_alert": bool(readable and user_tok),
            "can_publish_text": bool(is_configured_own),
            "can_publish_media": bool(is_configured_own and user_tok),
        }

        if accessible:
            return {
                "auth_status": "connected",
                "auth_error": None,
                "auth_capabilities": caps,
                "auth_checked_at": now,
                "resolved_external_id": str(group_id),
            }

        return {
            "auth_status": "invalid",
            "auth_error": last_err
            or (
                f"VK group {group_id} not accessible — "
                "для публикации укажите Group to post + community token; "
                "для чтения подключите user OAuth"
            ),
            "auth_capabilities": caps,
            "auth_checked_at": now,
            "resolved_external_id": str(group_id),
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

    async def sync_own_publish_flag(
        self,
        channel_id: int,
        *,
        role: str,
        auth_status: str,
        can_publish: Optional[bool] = None,
    ) -> bool:
        """Keep own.publish_enabled aligned with confirmed publish rights after recheck.

        Stale/bulk recheck used to only clear publish when disconnected, never restore
        it — channels looked Connected but could not be selected on Posts.
        For VK, auth_status may be connected for read while community token is dead —
        then can_publish=False must keep publish_enabled off.
        """
        if (role or "").lower() != "own":
            return False
        if can_publish is not None:
            enabled = bool(can_publish)
        else:
            enabled = auth_status == "connected"
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE smm_brand_channels
                    SET publish_enabled = %s
                    WHERE id = %s
                      AND role = 'own'
                      AND publish_enabled IS DISTINCT FROM %s
                    """,
                    (enabled, channel_id, enabled),
                )
                return cur.rowcount > 0
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
        caps = probe.get("auth_capabilities") or {}
        await self.sync_own_publish_flag(
            channel_id,
            role=str(ch.get("role") or "own"),
            auth_status=str(probe.get("auth_status") or "unknown"),
            can_publish=caps.get("can_publish_text") if isinstance(caps, dict) else None,
        )
        resolved = probe.get("resolved_external_id")
        if (
            ch.get("network") == "vk"
            and resolved
            and str(resolved) != str(ch.get("external_id") or "").strip()
        ):
            conn = await get_db_connection()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        UPDATE smm_brand_channels
                        SET external_id = %s
                        WHERE id = %s
                        """,
                        (str(resolved), channel_id),
                    )
            finally:
                await release_db_connection(conn)
            ch["external_id"] = str(resolved)
        # Reload so publish_enabled / auth fields match DB after sync.
        refreshed = await smm_service.get_channel(user_id, channel_id)
        return refreshed or {
            **ch,
            "auth_status": probe["auth_status"],
            "auth_error": probe.get("auth_error"),
            "auth_checked_at": (
                probe["auth_checked_at"].isoformat()
                if probe.get("auth_checked_at")
                else None
            ),
            "auth_capabilities": probe.get("auth_capabilities") or {},
            "publish_enabled": (
                True
                if (ch.get("role") == "own" and probe.get("auth_status") == "connected")
                else False
                if ch.get("role") == "own"
                else ch.get("publish_enabled")
            ),
        }

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
                caps = probe.get("auth_capabilities") or {}
                await self.sync_own_publish_flag(
                    int(ch["id"]),
                    role=str(ch.get("role") or "own"),
                    auth_status=str(probe.get("auth_status") or "unknown"),
                    can_publish=caps.get("can_publish_text") if isinstance(caps, dict) else None,
                )
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

        if net == "url":
            # URL sources do not publish themselves; targets are own TG/VK channels.
            return

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

        if updates.get("collect_enabled") is True and net in ("tg", "vk"):
            await self.require_platform(user_id, net, PlatformAction.COLLECT)

        if updates.get("alert_enabled") is True and net in ("tg", "vk"):
            await self.require_platform(user_id, net, PlatformAction.ALERT)

    async def get_onboarding_state(self, user_id: int) -> dict[str, Any]:
        from services.smm_service import smm_service
        from services.demo_seed_service import (
            get_user_utm_campaign,
            is_s01_campaign,
            seed_demo_workspace,
        )

        prefs = await system_settings_service.get_value(f"smm_onboarding_{user_id}", {})
        if not isinstance(prefs, dict):
            prefs = {}

        campaign = await get_user_utm_campaign(user_id)
        if is_s01_campaign(campaign) and not prefs.get("demo_seeded"):
            try:
                await seed_demo_workspace(user_id, campaign=campaign)
                prefs = await system_settings_service.get_value(
                    f"smm_onboarding_{user_id}", {}
                )
                if not isinstance(prefs, dict):
                    prefs = {}
            except Exception:
                pass

        platforms = await self.get_all_platform_status(user_id)
        brands = await smm_service.list_brands(user_id)
        channels = await smm_service.list_all_channels(user_id)
        own_channels = [c for c in channels if c.get("role") == "own"]
        # Real connected own (exclude demo-* external ids)
        from services.demo_seed_service import is_demo_external_id

        own_connected = [
            c
            for c in own_channels
            if c.get("auth_status") == "connected"
            and not is_demo_external_id(c.get("external_id"))
        ]
        own_real = [
            c for c in own_channels if not is_demo_external_id(c.get("external_id"))
        ]
        skipped = bool(prefs.get("skipped"))
        demo_seeded = bool(prefs.get("demo_seeded"))

        tg_ready = bool(platforms["tg"].get("connected"))
        vk_ready = bool(platforms["vk"].get("connected"))
        any_platform = any(
            bool((platforms.get(k) or {}).get("connected"))
            for k in ("tg", "vk", "instagram", "threads", "tw", "dzen", "wp")
        )
        has_brand = len(brands) > 0
        has_own_channel = len(own_real) > 0
        # Channel can be added without ownership; publish still needs connected.
        completed = skipped or has_own_channel

        step = 1
        if any_platform:
            step = 2
        if has_brand:
            step = 3
        if has_own_channel:
            step = 4
        if own_connected:
            step = 5

        learn_mode = demo_seeded and not bool(own_connected)

        return {
            "step": step,
            "total_steps": 5,
            "tg_ready": tg_ready,
            "vk_ready": vk_ready,
            "any_platform_ready": any_platform,
            "has_brand": has_brand,
            "has_own_channel": has_own_channel,
            "has_connected_own_channel": bool(own_connected),
            "skipped": skipped,
            "completed": completed,
            "platforms": platforms,
            "demo_seeded": demo_seeded,
            "demo_brand_id": prefs.get("demo_brand_id"),
            "learn_mode": learn_mode,
            "utm_campaign": campaign,
        }

    async def set_onboarding_skipped(self, user_id: int, skipped: bool = True) -> dict[str, Any]:
        prefs = await system_settings_service.get_value(f"smm_onboarding_{user_id}", {})
        if not isinstance(prefs, dict):
            prefs = {}
        prefs["skipped"] = skipped
        prefs["updated_at"] = datetime.utcnow().isoformat()
        await system_settings_service.set_value(f"smm_onboarding_{user_id}", prefs)
        return await self.get_onboarding_state(user_id)

    async def seed_demo_onboarding(self, user_id: int, force: bool = False) -> dict[str, Any]:
        from services.demo_seed_service import seed_demo_workspace

        result = await seed_demo_workspace(user_id, force=force)
        state = await self.get_onboarding_state(user_id)
        return {"seed": result, "state": state}

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
