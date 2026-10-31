"""RSS-ленты на своём канале: нормализация URL и текст записи."""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from shared.url_safety import UnsafeUrlError, validate_http_url_shape

MAX_RSS_FEEDS = 10
MAX_SEEN_IDS = 200
MIN_INTERVAL_MIN = 15
MAX_INTERVAL_MIN = 1440
MAX_SUFFIX_LEN = 300

_BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def parse_stored_rss_feeds(raw: Any) -> list[dict[str, Any]]:
    """Прочитать сохранённый JSON, не отбрасывая seen_ids."""
    data = raw
    if isinstance(raw, str):
        try:
            import json

            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(data, list):
        return []
    feeds: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        seen_raw = item.get("seen_ids")
        seen_ids = (
            [str(value) for value in seen_raw if str(value).strip()]
            if isinstance(seen_raw, list)
            else []
        )
        try:
            interval_min = int(item.get("interval_min") or 60)
        except (TypeError, ValueError):
            interval_min = 60
        interval_min = max(MIN_INTERVAL_MIN, min(MAX_INTERVAL_MIN, interval_min))
        feeds.append(
            {
                "url": url,
                "enabled": bool(item.get("enabled", True)),
                "interval_min": interval_min,
                "suffix": str(item.get("suffix") or "")[:MAX_SUFFIX_LEN],
                "seen_ids": seen_ids[-MAX_SEEN_IDS:],
                "last_run_at": item.get("last_run_at"),
            }
        )
    return feeds


def public_rss_feeds(raw: Any) -> list[dict[str, Any]]:
    """Поля ленты для API-экспорта: без истории seen_ids."""
    return [
        {
            "url": feed["url"],
            "enabled": feed["enabled"],
            "interval_min": feed["interval_min"],
            "suffix": feed["suffix"],
            "last_run_at": feed.get("last_run_at"),
        }
        for feed in parse_stored_rss_feeds(raw)
    ]


def merge_rss_feeds(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    """Собрать ленты из запроса и сохранить seen_ids уже известных URL."""
    if not isinstance(incoming, list):
        raise ValueError("rss_feeds must be a list")
    prior = {feed["url"]: feed for feed in parse_stored_rss_feeds(existing)}
    merged: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for raw in incoming:
        if isinstance(raw, str):
            raw = {"url": raw}
        if not isinstance(raw, dict):
            raise ValueError("RSS-лента должна быть объектом с url")
        try:
            url = validate_http_url_shape(str(raw.get("url") or ""))
        except UnsafeUrlError as exc:
            raise ValueError(f"Некорректный URL ленты: {exc}") from exc
        if url in seen_urls:
            continue
        seen_urls.add(url)
        prev = prior.get(url) or {}
        interval_raw = raw.get("interval_min", prev.get("interval_min", 60))
        try:
            interval_min = int(interval_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("interval_min должен быть целым числом") from exc
        if interval_min < MIN_INTERVAL_MIN or interval_min > MAX_INTERVAL_MIN:
            raise ValueError(
                f"Интервал RSS должен быть от {MIN_INTERVAL_MIN} до {MAX_INTERVAL_MIN} минут"
            )
        suffix = str(
            raw.get("suffix") if "suffix" in raw else prev.get("suffix") or ""
        ).strip()
        if len(suffix) > MAX_SUFFIX_LEN:
            raise ValueError("Подпись RSS слишком длинная")
        enabled = raw.get("enabled", True)
        merged.append(
            {
                "url": url,
                "enabled": bool(enabled),
                "interval_min": interval_min,
                "suffix": suffix,
                "seen_ids": list(prev.get("seen_ids") or []),
                "last_run_at": prev.get("last_run_at"),
            }
        )
    if len(merged) > MAX_RSS_FEEDS:
        raise ValueError(f"Не больше {MAX_RSS_FEEDS} RSS-лент на канал")
    return merged


def feed_is_due(feed: dict[str, Any], now: datetime) -> bool:
    """Лента включена и с прошлого запуска прошёл interval_min."""
    if not feed.get("enabled", True):
        return False
    if not str(feed.get("url") or "").strip():
        return False
    last_raw = feed.get("last_run_at")
    if not last_raw:
        return True
    try:
        last = datetime.fromisoformat(str(last_raw).replace("Z", "+00:00"))
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    try:
        interval_min = int(feed.get("interval_min") or 60)
    except (TypeError, ValueError):
        interval_min = 60
    interval_min = max(MIN_INTERVAL_MIN, min(MAX_INTERVAL_MIN, interval_min))
    current = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return current >= last + timedelta(minutes=interval_min)


def mark_feed_ran(feed: dict[str, Any], now: datetime, item_id: str | None = None) -> None:
    """Зафиксировать запуск и, если запись ушла в очередь, её id."""
    current = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    feed["last_run_at"] = current.astimezone(timezone.utc).isoformat()
    if not item_id:
        return
    seen = [str(value) for value in (feed.get("seen_ids") or []) if str(value).strip()]
    if item_id not in seen:
        seen.append(item_id)
    feed["seen_ids"] = seen[-MAX_SEEN_IDS:]


def rss_item_id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("link") or item.get("guid") or item.get("title") or "").strip()


def _plain(value: str, limit: int) -> str:
    text = html.unescape(value or "")
    text = _BLOCK_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def rss_item_text(item: dict[str, Any], suffix: str = "") -> str:
    """Заголовок, текст и ссылка без HTML — тело publish job."""
    title = _plain(str(item.get("title") or ""), 500)
    body = _plain(str(item.get("summary") or item.get("description") or ""), 4000)
    link = str(item.get("link") or "").strip()
    parts: list[str] = []
    if title:
        parts.append(title)
    if body and body not in title:
        parts.append(body)
    text = "\n\n".join(parts).strip()
    if link and link not in text:
        text = f"{text}\n\n{link}".strip() if text else link
    extra = (suffix or "").strip()
    if extra:
        text = f"{text}\n\n{extra}".strip()
    return text
