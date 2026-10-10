"""Hourly channel digest helpers (batch summary of held posts)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable, Optional, Sequence

DEFAULT_SUMMARY_PROMPT = (
    "Сделай краткую сводку: выдели главные темы и факты. "
    "Пиши связным текстом без нумерации источников."
)

DEFAULT_PROCESS_PROMPT = "Вычитай текст: исправь ошибки, сохрани смысл и факты."


def parse_channel_ids(raw: Any) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, str):
        import json

        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(raw, (list, tuple, set)):
        return []
    out: list[int] = []
    seen: set[int] = set()
    for item in raw:
        try:
            channel_id = int(item)
        except (TypeError, ValueError):
            continue
        if channel_id in seen:
            continue
        seen.add(channel_id)
        out.append(channel_id)
    return out


def clamp_interval_min(value: Any, *, default: int = 60) -> int:
    try:
        interval = int(value)
    except (TypeError, ValueError):
        interval = default
    return max(5, min(1440, interval))


def is_digest_due(
    last_run_at: Optional[datetime],
    interval_min: int,
    *,
    now: Optional[datetime] = None,
) -> bool:
    """True when the job has never run or the interval has elapsed."""
    current = now or datetime.utcnow()
    if last_run_at is None:
        return True
    stamped = last_run_at
    if stamped.tzinfo is not None:
        stamped = stamped.replace(tzinfo=None)
    current_naive = current.replace(tzinfo=None) if current.tzinfo else current
    return current_naive - stamped >= timedelta(minutes=max(5, int(interval_min)))


def channel_in_digest_sources(
    channel_id: Any,
    source_channel_ids: Iterable[int],
) -> bool:
    try:
        needle = int(channel_id)
    except (TypeError, ValueError):
        return False
    return needle in set(int(x) for x in source_channel_ids)


def build_digest_source_index(
    jobs: Sequence[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Map source channel_id → enabled digest job (first wins)."""
    index: dict[int, dict[str, Any]] = {}
    for job in jobs:
        if not job.get("enabled"):
            continue
        for channel_id in parse_channel_ids(job.get("source_channel_ids")):
            index.setdefault(channel_id, job)
    return index


def combine_digest_texts(
    posts: Sequence[dict[str, Any]],
    *,
    max_posts: int = 20,
    max_chars: int = 8000,
) -> str:
    chunks: list[str] = []
    for post in list(posts)[:max_posts]:
        text = str(post.get("post_text") or "").strip()
        if not text:
            continue
        domain = str(post.get("domain") or post.get("channel_id") or "source").strip()
        chunks.append(f"[{domain}]\n{text}")
    combined = "\n---\n".join(chunks)
    if len(combined) > max_chars:
        return combined[:max_chars]
    return combined


def should_create_digest(posts: Sequence[dict[str, Any]]) -> bool:
    """Empty hold set → no summary post."""
    return any(str(p.get("post_text") or "").strip() for p in posts)


def normalize_theme_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        import json

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                raw = parsed
            else:
                raw = [part.strip() for part in raw.split(",")]
        except (json.JSONDecodeError, TypeError):
            raw = [part.strip() for part in raw.split(",")]
    if not isinstance(raw, (list, tuple, set)):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        tag = str(item or "").strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append(tag)
    return out


def pick_cover_pack(
    packs: Sequence[dict[str, Any]],
    theme_tags: Sequence[str],
) -> Optional[dict[str, Any]]:
    """Pick media pack with max tag overlap; None if no intersection."""
    needles = set(normalize_theme_tags(list(theme_tags)))
    if not needles:
        return None
    best: Optional[dict[str, Any]] = None
    best_score = 0
    for pack in packs:
        keys = pack.get("object_keys") or []
        if not isinstance(keys, list) or not any(str(k).strip() for k in keys):
            continue
        pack_tags = set(normalize_theme_tags(pack.get("tags")))
        score = len(needles & pack_tags)
        if score > best_score:
            best_score = score
            best = pack
    return best if best_score > 0 else None


def cover_image_from_pack(pack: Optional[dict[str, Any]]) -> Optional[str]:
    if not pack:
        return None
    keys = pack.get("object_keys") or []
    if not isinstance(keys, list):
        return None
    for key in keys:
        value = str(key or "").strip()
        if value:
            return value
    return None


def should_notify_cover_miss(
    *,
    theme: str,
    last_theme: Optional[str],
    last_at: Optional[datetime],
    now: Optional[datetime] = None,
    cooldown_hours: int = 24,
) -> bool:
    """True when theme is new or cooldown elapsed since last miss notification."""
    theme_norm = (theme or "").strip().lower()
    if not theme_norm:
        return False
    current = now or datetime.utcnow()
    if current.tzinfo is not None:
        current = current.replace(tzinfo=None)
    last_norm = (last_theme or "").strip().lower()
    if last_norm != theme_norm:
        return True
    if last_at is None:
        return True
    stamped = last_at.replace(tzinfo=None) if last_at.tzinfo else last_at
    return current - stamped >= timedelta(hours=max(1, int(cooldown_hours)))


def parse_digest_ai_payload(raw: str) -> dict[str, Any]:
    """Parse AI response: JSON with summary/theme/tags or plain summary text."""
    import json
    import re

    text = (raw or "").strip()
    if not text:
        return {"summary": "", "theme": "", "tags": []}
    candidate = text
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            summary = str(data.get("summary") or data.get("text") or "").strip()
            theme = str(data.get("theme") or "").strip()
            tags = normalize_theme_tags(data.get("tags") or [])
            if theme and theme.lower() not in tags:
                tags = [theme.lower(), *tags]
            return {
                "summary": summary or text,
                "theme": theme or (tags[0] if tags else ""),
                "tags": tags,
            }
    except (json.JSONDecodeError, TypeError):
        pass
    return {"summary": text, "theme": "", "tags": []}
