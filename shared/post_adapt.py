"""Единая адаптация текста поста под целевые соцсети (SMM + classic processor).

Канонические ключи сетей: tg|vk|tw|threads|instagram|dzen|wp.
Лимиты объявлены здесь один раз; core/processor/боты re-export или импортируют.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Iterable, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

# Soft/hard length caps — single source of truth
NETWORK_TEXT_LIMITS: dict[str, int] = {
    "tg": 4096,
    "vk": 15985,
    "tw": 280,
    "threads": 500,
    "instagram": 2200,
    "dzen": 1500,
    "wp": 150000,
}

# Long names used in posts.platform_texts / processor PLATFORM_FLAGS
NETWORK_TO_PLATFORM_TEXT_KEY: dict[str, str] = {
    "tg": "telegram",
    "vk": "vkontakte",
    "tw": "twitter",
    "wp": "wordpress",
    "threads": "threads",
    "dzen": "dzen",
    "instagram": "instagram",
}

PLATFORM_TEXT_KEY_TO_NETWORK: dict[str, str] = {
    v: k for k, v in NETWORK_TO_PLATFORM_TEXT_KEY.items()
}

NETWORK_KEY_ALIASES: dict[str, str] = {
    "telegram": "tg",
    "vkontakte": "vk",
    "twitter": "tw",
    "x": "tw",
    "wordpress": "wp",
    "insta": "instagram",
    "ig": "instagram",
    "zen": "dzen",
}

ADAPT_NETWORKS = frozenset(NETWORK_TEXT_LIMITS.keys())

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize_network(raw: str | None) -> str:
    value = (raw or "").lower().strip()
    if not value:
        return ""
    return NETWORK_KEY_ALIASES.get(value, value)


def network_text_limit(raw: str | None) -> int | None:
    net = normalize_network(raw)
    return NETWORK_TEXT_LIMITS.get(net)


def to_plain(text: str) -> str:
    """Strip HTML tags and common entities; return trimmed plain text."""
    if not text:
        return ""
    plain = _HTML_TAG_RE.sub("", text)
    plain = plain.replace("&nbsp;", " ").replace("&amp;", "&")
    plain = plain.replace("&lt;", "<").replace("&gt;", ">")
    return plain.strip()


def hard_truncate(text: str, max_length: int) -> str:
    if not text or max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length]


async def fit_text(
    text: str,
    network: str,
    *,
    prefer_summarize: bool = False,
    max_length: int | None = None,
) -> str:
    """Ensure text fits network limit; optionally AI-summarize when oversize."""
    net = normalize_network(network)
    limit = max_length if max_length is not None else NETWORK_TEXT_LIMITS.get(net)
    if limit is None:
        return text or ""
    if not text or len(text) <= limit:
        return text or ""

    if prefer_summarize:
        try:
            from shared.ai_client import summarize

            result = await summarize(text, limit)
            return hard_truncate(result or "", limit)
        except Exception as exc:
            logger.warning("fit_text summarize fallback for %s: %s", net, exc)

    return hard_truncate(text, limit)


def _append_static_html(text: str, static_html: str, max_length: int) -> str:
    if not static_html:
        return text
    combined = text + "\n" + static_html
    if len(combined) <= max_length:
        return combined
    return text


def _networks_from_input(
    networks: Iterable[str] | None = None,
    targets: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    raw_items: list[str] = []
    if networks:
        raw_items.extend(str(n) for n in networks)
    if targets:
        for t in targets:
            raw_items.append(str(t.get("network") or ""))
    for raw in raw_items:
        net = normalize_network(raw)
        if not net or net not in ADAPT_NETWORKS or net in seen:
            continue
        seen.add(net)
        ordered.append(net)
    return ordered


async def adapt_for_networks(
    text: str,
    media: list[str] | None = None,
    *,
    networks: Iterable[str] | None = None,
    targets: Sequence[Mapping[str, Any]] | None = None,
    keep_html_for: Sequence[str] = ("tg",),
    static_html: str | None = None,
    prefer_summarize: bool = False,
) -> dict[str, dict[str, Any]]:
    """Build per-network adapter payloads with text already fitted to limits.

    Returns short-key dict, e.g. ``{"tg": {"text": ..., "parse_mode": "HTML", ...}}``.
    """
    media_list = list(media or [])
    keep_html = {normalize_network(n) for n in keep_html_for}
    nets = _networks_from_input(networks=networks, targets=targets)
    plain = to_plain(text)
    result: dict[str, dict[str, Any]] = {}

    for net in nets:
        limit = NETWORK_TEXT_LIMITS[net]
        use_html = net in keep_html
        base = text if use_html else plain
        fitted = await fit_text(base, net, prefer_summarize=prefer_summarize)
        if static_html:
            fitted = _append_static_html(fitted, static_html, limit)

        if net == "tg":
            result["tg"] = {
                "text": fitted,
                "parse_mode": "HTML" if use_html else None,
                "keep_spoiler": True,
                "media": media_list,
            }
        elif net == "vk":
            result["vk"] = {
                "text": fitted,
                "attachments_mode": (
                    "carousel" if len(media_list) > 1 else ("single" if media_list else "none")
                ),
                "media": media_list,
                "poll_hint": False,
            }
        else:
            result[net] = {
                "text": fitted,
                "media": media_list,
            }

    return result


def adapters_to_platform_texts(adapters: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Map short-key adapters to long-key platform_texts for posts table."""
    out: dict[str, str] = {}
    for net, payload in adapters.items():
        if not isinstance(payload, dict):
            continue
        key = NETWORK_TO_PLATFORM_TEXT_KEY.get(normalize_network(net), net)
        text = payload.get("text")
        if text is None:
            continue
        out[key] = str(text)
    return out


async def prepare_platform_texts(
    text: str,
    post_flags: Mapping[str, bool],
    *,
    flag_to_network: Mapping[str, str],
    is_add_static_html: bool = False,
    static_html_content: Optional[str] = None,
    prefer_summarize: bool = True,
    keep_html_for: Sequence[str] = ("tg",),
) -> dict[str, str]:
    """Processor-facing helper: flags → fitted platform_texts (long keys)."""
    networks = [
        flag_to_network[flag]
        for flag, active in post_flags.items()
        if active and flag in flag_to_network
    ]
    static = static_html_content if is_add_static_html else None
    adapters = await adapt_for_networks(
        text,
        media=[],
        networks=networks,
        keep_html_for=keep_html_for,
        static_html=static,
        prefer_summarize=prefer_summarize,
    )
    return adapters_to_platform_texts(adapters)
