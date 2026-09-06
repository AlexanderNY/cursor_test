"""Load SMM brand channel flow config for WordPress collect/publish."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)

_NETWORK_TO_SERVICE = {
    "tg": "telegram",
    "telegram": "telegram",
    "vk": "vkontakte",
    "vkontakte": "vkontakte",
    "wp": "wordpress",
    "wordpress": "wordpress",
    "tw": "twitter",
    "twitter": "twitter",
    "threads": "threads",
    "dzen": "dzen",
    "instagram": "instagram",
}


def normalize_site_url(value: str) -> str:
    """Normalize WP site URL for matching external_id ↔ profile.site_url."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    if not raw.lower().startswith(("http://", "https://")):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "https").lower()
    netloc = (parsed.netloc or "").lower()
    path = (parsed.path or "").rstrip("/")
    if not netloc:
        return raw.rstrip("/").lower()
    return f"{scheme}://{netloc}{path}".rstrip("/")


def site_urls_match(a: str, b: str) -> bool:
    return normalize_site_url(a) == normalize_site_url(b) and bool(normalize_site_url(a))


def _parse_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def _parse_id_list(value: Any) -> List[int]:
    raw = _parse_json(value, [])
    if not isinstance(raw, list):
        return []
    out: List[int] = []
    for item in raw:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


def _parse_str_list(value: Any) -> List[str]:
    raw = _parse_json(value, [])
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        s = str(item or "").strip()
        if s:
            out.append(s)
    return out


def _row_to_channel(row: tuple, columns: List[str]) -> Dict[str, Any]:
    raw = dict(zip(columns, row))
    mode = (raw.get("conditions_mode") or "any_of").strip()
    if mode not in ("any_of", "all_of", "regex"):
        mode = "any_of"
    return {
        "id": int(raw["id"]),
        "brand_id": int(raw["brand_id"]) if raw.get("brand_id") is not None else None,
        "user_id": int(raw["user_id"]),
        "network": raw.get("network") or "wp",
        "external_id": str(raw.get("external_id") or "").strip(),
        "title": raw.get("title"),
        "role": raw.get("role") or "source",
        "collect_enabled": bool(raw.get("collect_enabled")),
        "alert_enabled": bool(raw.get("alert_enabled")),
        "publish_enabled": bool(raw.get("publish_enabled")),
        "save_conditions": _parse_json(raw.get("save_conditions"), []) or [],
        "conditions_mode": mode,
        "processing": _parse_json(raw.get("processing"), {}) or {},
        "publish_targets": _parse_id_list(raw.get("publish_targets")),
    }


async def list_wp_flow_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """WP brand channels with collect and/or publish enabled."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            where = [
                "c.network = 'wp'",
                (
                    "(COALESCE(c.collect_enabled, FALSE) = TRUE "
                    "OR COALESCE(c.publish_enabled, FALSE) = TRUE)"
                ),
            ]
            params: list[Any] = []
            if user_id is not None:
                where.append("b.user_id = %s")
                params.append(user_id)
            await cur.execute(
                f"""
                SELECT c.id, c.brand_id, b.user_id, c.network, c.external_id, c.title, c.role,
                       c.collect_enabled, c.alert_enabled, c.publish_enabled,
                       c.save_conditions, c.conditions_mode, c.processing, c.publish_targets
                FROM smm_brand_channels c
                JOIN smm_brands b ON b.id = c.brand_id
                WHERE {' AND '.join(where)}
                """,
                params,
            )
            rows = await cur.fetchall()
            if not rows:
                return []
            columns = [col.name for col in cur.description]
            return [_row_to_channel(r, columns) for r in rows]
    except Exception as exc:
        logger.debug("list_wp_flow_channels failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


async def list_wp_collect_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """WP brand channels with collect_enabled."""
    channels = await list_wp_flow_channels(user_id)
    return [c for c in channels if c.get("collect_enabled")]


async def list_wp_publish_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Own WP brand channels with publish_enabled."""
    channels = await list_wp_flow_channels(user_id)
    return [
        c
        for c in channels
        if c.get("publish_enabled") and (c.get("role") or "source") == "own"
    ]


async def resolve_publish_targets(
    brand_id: int,
    target_ids: List[int],
) -> List[Dict[str, Any]]:
    """Resolve BrandChannel ids to external_id + network for publish."""
    ids = [int(x) for x in target_ids if x is not None]
    if not ids or not brand_id:
        return []
    placeholders = ", ".join(["%s"] * len(ids))
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, network, external_id, title, publish_enabled
                FROM smm_brand_channels
                WHERE brand_id = %s AND id IN ({placeholders}) AND role = 'own'
                """,
                (brand_id, *ids),
            )
            rows = await cur.fetchall()
            result: List[Dict[str, Any]] = []
            for row in rows:
                ext = str(row[2] or "").strip()
                if not ext:
                    continue
                result.append(
                    {
                        "id": int(row[0]),
                        "network": (row[1] or "wp").lower(),
                        "external_id": ext,
                        "title": row[3],
                        "publish_enabled": bool(row[4]) if row[4] is not None else True,
                    }
                )
            return result
    except Exception as exc:
        logger.debug("resolve_publish_targets failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


def publish_targets_to_destination_fields(targets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map resolved targets → to_* flags + target_channels / target_groups."""
    tg_ids: List[str] = []
    vk_ids: List[str] = []
    wp_ids: List[str] = []
    services: List[str] = []
    flags = {
        "to_tg": False,
        "to_tw": False,
        "to_wp": False,
        "to_vk": False,
        "to_threads": False,
        "to_dzen": False,
        "to_instagram": False,
    }
    for t in targets:
        if t.get("publish_enabled") is False:
            continue
        ext = str(t.get("external_id") or "").strip()
        if not ext:
            continue
        net = str(t.get("network") or "").strip().lower()
        svc = _NETWORK_TO_SERVICE.get(net)
        if net in ("tg", "telegram"):
            tg_ids.append(ext)
            flags["to_tg"] = True
        elif net in ("vk", "vkontakte"):
            vk_ids.append(ext)
            flags["to_vk"] = True
        elif net in ("wp", "wordpress"):
            wp_ids.append(ext)
            flags["to_wp"] = True
        elif net in ("tw", "twitter"):
            flags["to_tw"] = True
        elif net == "threads":
            flags["to_threads"] = True
        elif net == "dzen":
            flags["to_dzen"] = True
        elif net == "instagram":
            flags["to_instagram"] = True
        if svc and svc not in services:
            services.append(svc)
    # WP destinations live in target_channels alongside TG ids (site URLs).
    target_channels = [*tg_ids, *wp_ids]
    return {
        **flags,
        "target_channels": target_channels,
        "target_groups": vk_ids,
        "process_services": services,
    }


async def load_wp_publish_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Load wp_publish_profile credentials for user."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT site_url, username, app_password, publish_enabled
                FROM wp_publish_profile
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            columns = [col.name for col in cur.description]
            return dict(zip(columns, row))
    except Exception as exc:
        logger.debug("load_wp_publish_profile failed: %s", exc)
        return None
    finally:
        await release_db_connection(conn)


def credentials_match_site(profile: Dict[str, Any], site_url: str) -> bool:
    """True if profile has complete credentials and site matches (or profile has no site)."""
    site = str(profile.get("site_url") or "").strip()
    user = str(profile.get("username") or "").strip()
    password = str(profile.get("app_password") or "").strip()
    if not site or not user or not password:
        return False
    needle = normalize_site_url(site_url)
    if not needle:
        return True
    return site_urls_match(site, needle)


async def resolve_credentials_for_site(
    user_id: int,
    site_url: str,
) -> Optional[Dict[str, str]]:
    """Resolve WP REST credentials for a site (channel external_id)."""
    profile = await load_wp_publish_profile(user_id)
    if not profile:
        return None
    site = str(site_url or "").strip() or str(profile.get("site_url") or "").strip()
    if site and not credentials_match_site(profile, site):
        # Profile is bound to another site — refuse mismatch.
        if normalize_site_url(str(profile.get("site_url") or "")):
            return None
    user = str(profile.get("username") or "").strip()
    password = str(profile.get("app_password") or "").strip()
    resolved_site = site or str(profile.get("site_url") or "").strip()
    if not resolved_site or not user or not password:
        return None
    return {
        "site_url": resolved_site,
        "username": user,
        "app_password": password,
    }


def post_target_sites(post: Dict[str, Any]) -> List[str]:
    """Extract WP site URLs from post.target_channels."""
    return _parse_str_list(post.get("target_channels"))
