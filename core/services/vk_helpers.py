"""Shared VK id / API response helpers (API 5.131+)."""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse


_CLUB_PREFIXES = ("club", "public", "event")
_VK_HOSTS = {"vk.com", "www.vk.com", "m.vk.com", "vk.ru", "www.vk.ru", "m.vk.ru"}


def parse_vk_group_id(value: Any) -> Optional[int]:
    """Positive numeric community id from int, club123, -123, or vk.com URL path."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    lower = s.lower()
    if lower.startswith(("http://", "https://")):
        try:
            parsed = urlparse(s)
        except Exception:
            return None
        host = (parsed.netloc or "").lower()
        if host not in _VK_HOSTS:
            return None
        path = (parsed.path or "").strip("/")
        if not path:
            return None
        s = path.split("/")[0].strip()
        lower = s.lower()

    if s.startswith("-"):
        s = s[1:].strip()
        lower = s.lower()

    for prefix in _CLUB_PREFIXES:
        if lower.startswith(prefix) and len(s) > len(prefix):
            rest = s[len(prefix) :]
            if rest.isdigit():
                s = rest
                break

    try:
        n = int(s)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n


def extract_vk_screen_name(value: Any) -> Optional[str]:
    """Screen name (short name) from raw id / URL when not a numeric club id."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if parse_vk_group_id(s) is not None:
        return None

    lower = s.lower()
    if lower.startswith(("http://", "https://")):
        try:
            parsed = urlparse(s)
        except Exception:
            return None
        host = (parsed.netloc or "").lower()
        if host not in _VK_HOSTS:
            return None
        path = (parsed.path or "").strip("/")
        s = path.split("/")[0].strip() if path else ""

    s = s.lstrip("@").strip()
    if not s or s.startswith("-"):
        return None
    if parse_vk_group_id(s) is not None:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.]+", s):
        return None
    return s


def groups_from_get_by_id(response: Any) -> list[dict[str, Any]]:
    """Normalize groups.getById response (legacy list or 5.131+ {groups, profiles})."""
    if isinstance(response, list):
        return [g for g in response if isinstance(g, dict) and g.get("id") is not None]
    if isinstance(response, dict):
        groups = response.get("groups")
        if isinstance(groups, list):
            return [g for g in groups if isinstance(g, dict) and g.get("id") is not None]
        if response.get("id") is not None:
            return [response]
    return []
