"""Sync SMM URL source channels with curl_settings.urls[] (url-bot pipeline)."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from services.profile_service import profile_service


def empty_curl_url_item(
    item_id: str,
    title: Optional[str] = None,
    initial_url: Optional[str] = None,
) -> dict[str, Any]:
    """Blank CurlUrlItem linked to an SMM URL channel."""
    url = (initial_url or "").strip()
    return {
        "id": item_id,
        "url": url,
        "xpath": "",
        "take_screenshot": False,
        "screenshot_format": "base64",
        "target_social_networks": {"tg": False, "tw": False, "vk": False, "wp": False},
        "target_channels": [],
        "target_groups": [],
        "schedule_time": "09:00",
        "run_once": False,
        "process_before_publish": False,
        "process_description": "",
        "remove_emojis": False,
        "remove_images": False,
        "clean_html": False,
        "process_services": [],
        "status_review_after_process": False,
        "add_static_html": False,
        "static_html_content": None,
        "screenshot_only": False,
        "title": title or "",
    }


async def ensure_curl_url_item(
    user_id: int,
    item_id: str,
    title: Optional[str] = None,
    initial_url: Optional[str] = None,
) -> dict[str, Any]:
    """Ensure curl_settings exists and contains urls[] item with given id."""
    settings = await profile_service.get_curl_settings(user_id)
    if not settings:
        item = empty_curl_url_item(item_id, title, initial_url=initial_url)
        return await profile_service.save_curl_settings(
            user_id,
            {"collect_enabled": False, "urls": [item]},
        )
    urls = list(settings.get("urls") or [])
    if any(str((u or {}).get("id") or "") == item_id for u in urls if isinstance(u, dict)):
        return settings
    urls.append(empty_curl_url_item(item_id, title, initial_url=initial_url))
    return await profile_service.save_curl_settings(
        user_id,
        {
            **settings,
            "urls": urls,
            "collect_enabled": bool(settings.get("collect_enabled")),
        },
    )


async def remove_curl_url_item(user_id: int, item_id: str) -> None:
    """Remove urls[] item by id; no-op if settings missing."""
    settings = await profile_service.get_curl_settings(user_id)
    if not settings:
        return
    urls = [
        u
        for u in (settings.get("urls") or [])
        if isinstance(u, dict) and str(u.get("id") or "") != item_id
    ]
    await profile_service.save_curl_settings(
        user_id,
        {
            **settings,
            "urls": urls,
            "collect_enabled": bool(settings.get("collect_enabled")) and bool(urls),
        },
    )


async def get_curl_url_item(user_id: int, item_id: str) -> Optional[dict[str, Any]]:
    settings = await profile_service.get_curl_settings(user_id)
    if not settings:
        return None
    for u in settings.get("urls") or []:
        if isinstance(u, dict) and str(u.get("id") or "") == item_id:
            return u
    return None


def _resolve_publish_targets_to_curl(
    brand_channels: list[dict[str, Any]],
    publish_target_ids: list[int],
) -> tuple[dict[str, bool], list[str], list[str]]:
    """Map own TG/VK channel ids → curl target flags + external_ids."""
    id_set = {int(x) for x in publish_target_ids}
    tg_ext: list[str] = []
    vk_ext: list[str] = []
    for ch in brand_channels:
        try:
            cid = int(ch.get("id"))
        except (TypeError, ValueError):
            continue
        if cid not in id_set:
            continue
        if ch.get("role") != "own":
            continue
        ext = str(ch.get("external_id") or "").strip()
        if not ext:
            continue
        net = str(ch.get("network") or "").lower()
        if net == "tg":
            tg_ext.append(ext)
        elif net == "vk":
            vk_ext.append(ext)
    # dedupe preserve order
    def uniq(xs: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in xs:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    tg_ext = uniq(tg_ext)
    vk_ext = uniq(vk_ext)
    flags = {
        "tg": bool(tg_ext),
        "tw": False,
        "vk": bool(vk_ext),
        "wp": False,
    }
    return flags, tg_ext, vk_ext


async def sync_url_channel_to_curl(
    user_id: int,
    channel: dict[str, Any],
    *,
    url_config: Optional[dict[str, Any]] = None,
    brand_channels: Optional[list[dict[str, Any]]] = None,
    any_url_collect_enabled: Optional[bool] = None,
) -> dict[str, Any]:
    """
    Merge channel + optional url_config into curl_settings.urls[id].
    Returns the updated curl url item.
    """
    item_id = str(channel.get("external_id") or "").strip()
    if not item_id:
        raise ValueError("URL channel missing external_id")

    settings = await profile_service.get_curl_settings(user_id)
    if not settings:
        await ensure_curl_url_item(user_id, item_id, channel.get("title"))
        settings = await profile_service.get_curl_settings(user_id) or {
            "collect_enabled": False,
            "urls": [],
        }

    urls = list(settings.get("urls") or [])
    idx = next(
        (
            i
            for i, u in enumerate(urls)
            if isinstance(u, dict) and str(u.get("id") or "") == item_id
        ),
        -1,
    )
    base = empty_curl_url_item(item_id, channel.get("title"))
    if idx >= 0 and isinstance(urls[idx], dict):
        base = {**base, **urls[idx], "id": item_id}

    if url_config:
        for key in (
            "url",
            "xpath",
            "schedule_time",
            "run_once",
            "take_screenshot",
            "screenshot_format",
            "process_before_publish",
            "process_description",
            "remove_emojis",
            "remove_images",
            "clean_html",
            "process_services",
            "status_review_after_process",
            "add_static_html",
            "static_html_content",
            "screenshot_only",
        ):
            if key in url_config:
                base[key] = url_config[key]

    publish_targets = channel.get("publish_targets") or []
    if not isinstance(publish_targets, list):
        publish_targets = []
    target_ids = [
        int(x)
        for x in publish_targets
        if isinstance(x, (int, float)) or str(x).isdigit()
    ]
    if brand_channels is not None:
        flags, tg_ext, vk_ext = _resolve_publish_targets_to_curl(brand_channels, target_ids)
        base["target_social_networks"] = {
            **(base.get("target_social_networks") or {}),
            **flags,
        }
        base["target_channels"] = tg_ext
        base["target_groups"] = vk_ext

    if idx >= 0:
        urls[idx] = base
    else:
        urls.append(base)

    collect_enabled = bool(settings.get("collect_enabled"))
    if any_url_collect_enabled is not None:
        collect_enabled = bool(any_url_collect_enabled)
    elif channel.get("collect_enabled"):
        collect_enabled = True

    await profile_service.save_curl_settings(
        user_id,
        {
            **settings,
            "urls": urls,
            "collect_enabled": collect_enabled,
        },
    )
    return base


def new_url_channel_external_id() -> str:
    return str(uuid.uuid4())
