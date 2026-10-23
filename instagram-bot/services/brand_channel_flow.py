"""Load SMM brand channel flow config for Instagram collect and publish targets."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

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
    "instagram": "instagram",
    "ig": "instagram",
}

_HANDLE_FROM_URL = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/@?([A-Za-z0-9._]{1,30})(?:/|$|\?|#)",
    re.IGNORECASE,
)
_HANDLE_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


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


def normalize_instagram_handle(external_id: str) -> Optional[str]:
    """
    Brand channel external_id → username without @.

    Accepts @name, name, https://instagram.com/name, or numeric pk.
    """
    raw = str(external_id or "").strip()
    if not raw:
        return None
    match = _HANDLE_FROM_URL.search(raw)
    if match:
        return match.group(1)
    if raw.startswith("@"):
        raw = raw[1:].strip()
    raw = raw.split("/")[0].split("?")[0].split("#")[0].strip()
    if not raw:
        return None
    if raw.isdigit():
        return raw
    if _HANDLE_RE.fullmatch(raw):
        return raw
    return None


def _row_to_channel(row: tuple, columns: List[str]) -> Dict[str, Any]:
    raw = dict(zip(columns, row))
    mode = (raw.get("conditions_mode") or "any_of").strip()
    if mode not in ("any_of", "all_of", "regex"):
        mode = "any_of"
    return {
        "id": int(raw["id"]),
        "brand_id": int(raw["brand_id"]) if raw.get("brand_id") is not None else None,
        "user_id": int(raw["user_id"]),
        "network": raw.get("network") or "instagram",
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
        "alert_delivery": _parse_json(raw.get("alert_delivery"), {}) or {},
        "alert_rules": _parse_json(raw.get("alert_rules"), []) or [],
    }


async def list_instagram_flow_channels(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Instagram brand channels with collect enabled."""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cur:
            where = [
                "c.network = 'instagram'",
                "COALESCE(c.collect_enabled, FALSE) = TRUE",
            ]
            params: list[Any] = []
            if user_id is not None:
                where.append("b.user_id = %s")
                params.append(user_id)
            await cur.execute(
                f"""
                SELECT c.id, c.brand_id, b.user_id, c.network, c.external_id, c.title, c.role,
                       c.collect_enabled, c.alert_enabled, c.publish_enabled,
                       c.save_conditions, c.conditions_mode, c.processing, c.publish_targets,
                       c.alert_delivery, c.alert_rules
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
        logger.debug("list_instagram_flow_channels failed: %s", exc)
        return []
    finally:
        await release_db_connection(conn)


async def resolve_publish_targets(
    brand_id: int,
    target_ids: List[int],
) -> List[Dict[str, Any]]:
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
                        "network": (row[1] or "instagram").lower(),
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
        elif net in ("tw", "twitter", "x"):
            flags["to_tw"] = True
        elif net in ("threads",):
            flags["to_threads"] = True
        elif net in ("instagram", "ig"):
            flags["to_instagram"] = True
        if svc and svc not in services:
            services.append(svc)
    return {
        **flags,
        "target_channels": [*tg_ids, *wp_ids],
        "target_groups": vk_ids,
        "process_services": services,
    }
