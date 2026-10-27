"""Learn article backup files: JSON catalog or a zip with learn_seed.json."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

MAX_BACKUP_BYTES = 20 * 1024 * 1024
MAX_POSTS = 500
_EXPORT_DROP = frozenset({"id", "updatedAt", "createdAt", "updated_at", "created_at"})
_PREFERRED_ZIP_NAMES = ("learn_seed.json", "posts.json")


def build_export(posts: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned: list[dict[str, Any]] = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        cleaned.append({key: value for key, value in post.items() if key not in _EXPORT_DROP})
    return {
        "kind": "learn-articles",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(cleaned),
        "posts": cleaned,
    }


def parse_learn_backup(payload: bytes, filename: str = "") -> list[dict[str, Any]]:
    if len(payload) > MAX_BACKUP_BYTES:
        raise ValueError("Файл больше 20 МБ")
    if not payload:
        raise ValueError("Файл пустой")
    name = (filename or "").lower()
    if name.endswith(".zip") or payload.startswith(b"PK"):
        return _posts_from_zip(payload)
    try:
        data = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Файл не JSON и не zip с learn_seed.json") from exc
    return _posts_from_json(data)


def _posts_from_zip(payload: bytes) -> list[dict[str, Any]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise ValueError("Архив повреждён") from exc
    with archive:
        names = [
            info.filename
            for info in archive.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".json")
        ]
        chosen = ""
        for preferred in _PREFERRED_ZIP_NAMES:
            match = next((name for name in names if name.replace("\\", "/").endswith(preferred)), "")
            if match:
                chosen = match
                break
        if not chosen:
            raise ValueError("В архиве нужен learn_seed.json или posts.json")
        info = archive.getinfo(chosen)
        if info.file_size > MAX_BACKUP_BYTES:
            raise ValueError("Файл статей в архиве больше 20 МБ")
        raw = archive.read(chosen)
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Файл статей в архиве не JSON") from exc
    return _posts_from_json(data)


def _posts_from_json(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        posts = data
    elif isinstance(data, dict) and isinstance(data.get("posts"), list):
        posts = data["posts"]
    elif isinstance(data, dict) and data.get("slug") and data.get("title"):
        posts = [data]
    else:
        raise ValueError("Ожидается список статей или объект с полем posts")
    if not posts:
        raise ValueError("В файле нет статей")
    if len(posts) > MAX_POSTS:
        raise ValueError(f"В файле больше {MAX_POSTS} статей")
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(posts, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Статья {index} должна быть объектом")
        slug = str(item.get("slug") or "").strip()
        title = str(item.get("title") or "").strip()
        if not slug or not title:
            raise ValueError(f"У статьи {index} нужны slug и title")
        if slug in seen:
            cleaned = [row for row in cleaned if str(row.get("slug")) != slug]
        seen.add(slug)
        cleaned.append(item)
    return cleaned
