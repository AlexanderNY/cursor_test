"""Canonical SMM channel networks and aliases."""

from __future__ import annotations

from typing import FrozenSet

from shared.post_adapt import (
    ADAPT_NETWORKS,
    NETWORK_KEY_ALIASES,
    NETWORK_TEXT_LIMITS,
    network_text_limit as _shared_network_text_limit,
    normalize_network as _shared_normalize_network,
)

# Stored in smm_brand_channels.network / inbox / job targets
CANONICAL_NETWORKS: FrozenSet[str] = frozenset(
    {
        "tg",
        "vk",
        "url",
        "instagram",
        "threads",
        "tw",
        "dzen",
        "wp",
    }
)

# Inbox ingest currently wired for TG/VK; others accepted for API/UI filters
INBOX_NETWORKS: FrozenSet[str] = CANONICAL_NETWORKS - {"url"}

# Re-export shared aliases + limits (single source of truth in shared.post_adapt)
NETWORK_ALIASES: dict[str, str] = dict(NETWORK_KEY_ALIASES)

SETUP_URLS: dict[str, str] = {
    "tg": "/telegram",
    "vk": "/vkontakte",
    "instagram": "/instagram",
    "threads": "/threads",
    "tw": "/twitter",
    "dzen": "/dzen",
    "wp": "/wordpress",
    "url": "/custom-url",
}

NETWORK_LABELS: dict[str, str] = {
    "tg": "Telegram",
    "vk": "VKontakte",
    "url": "URL",
    "instagram": "Instagram",
    "threads": "Threads",
    "tw": "Twitter",
    "dzen": "Дзен",
    "wp": "WordPress",
}

# Map channel network → processor / post_service flags
NETWORK_TO_FLAG: dict[str, str] = {
    "tg": "to_tg",
    "vk": "to_vk",
    "tw": "to_tw",
    "wp": "to_wp",
    "threads": "to_threads",
    "dzen": "to_dzen",
    "instagram": "to_instagram",
}

def normalize_network(raw: str | None) -> str:
    return _shared_normalize_network(raw)


def is_allowed_network(raw: str | None) -> bool:
    return normalize_network(raw) in CANONICAL_NETWORKS


def is_inbox_network(raw: str | None) -> bool:
    return normalize_network(raw) in INBOX_NETWORKS


def network_label(raw: str | None) -> str:
    net = normalize_network(raw)
    return NETWORK_LABELS.get(net, (raw or "").upper() or "—")


def setup_url(raw: str | None) -> str:
    net = normalize_network(raw)
    return SETUP_URLS.get(net, "/channels")


def network_text_limit(raw: str | None) -> int | None:
    return _shared_network_text_limit(raw)


def is_adapt_network(raw: str | None) -> bool:
    return normalize_network(raw) in ADAPT_NETWORKS
