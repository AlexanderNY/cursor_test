"""Чистые правила портфолио: адрес, кейс, публикация, сезоны Cert, GitHub."""
from __future__ import annotations

import re
from typing import Any, Optional
from uuid import UUID

MAX_CASES = 6
MAX_STACK = 12
MAX_LEARN_SLUGS = 8
MAX_HEADLINE = 160
MAX_SUMMARY = 2000
MAX_TITLE = 160
MAX_ROLE = 120
MAX_BODY = 2000
MAX_STACK_ITEM = 40
MAX_URL = 500
MAX_BLURB = 400
MAX_PHONE = 64
MAX_EMAIL = 255
MAX_COVER_BYTES = 1_500_000
ABOUT_EXCERPT = 600
CERT_QUIZ_PERCENT = 70

HANDLE_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,30}[a-z0-9])$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?$")
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TAG_RE = re.compile(r"<[^>]*>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

RESERVED_HANDLES = frozenset(
    {
        "admin",
        "api",
        "cases",
        "files",
        "health",
        "me",
        "new",
        "p",
        "portfolio",
        "public",
        "sources",
    }
)

CERT_TRACKS: tuple[tuple[str, str], ...] = (
    ("b", "Сезон B · Первое приложение"),
    ("s01", "Сезон 1 · Слои и стенд"),
    ("py", "Python · Junior → Senior"),
    ("qa", "QA · Junior → Senior"),
    ("map", "Карта · листья собеса"),
)

_TRACK_TITLES = {track_id: title for track_id, title in CERT_TRACKS}


def clean_text(raw: object, *, max_len: int, allow_newlines: bool) -> str:
    text = str(raw or "").replace("\r\n", "\n").replace("\r", "\n")
    if not allow_newlines:
        text = text.replace("\n", " ")
    text = _CONTROL_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    if allow_newlines:
        text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:max_len]


def normalize_handle(raw: object) -> str:
    handle = clean_text(raw, max_len=32, allow_newlines=False).lower()
    if handle in RESERVED_HANDLES:
        raise ValueError("Этот адрес зарезервирован")
    if not HANDLE_RE.match(handle):
        raise ValueError("Адрес: 3–32 символа, латиница, цифры и дефис")
    return handle


def parse_optional_uuid(raw: object) -> Optional[str]:
    text = clean_text(raw, max_len=64, allow_newlines=False)
    if not text:
        return None
    try:
        return str(UUID(text))
    except ValueError as exc:
        raise ValueError("Некорректный id резюме") from exc


def normalize_email(raw: object) -> str:
    email = clean_text(raw, max_len=MAX_EMAIL, allow_newlines=False)
    if not email:
        return ""
    if not EMAIL_RE.match(email):
        raise ValueError("Некорректный email")
    return email


def image_mime(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12:
        raise ValueError("Файл не похож на картинку")
    if len(data) > MAX_COVER_BYTES:
        raise ValueError("Картинка больше 1.5 МБ")
    blob = bytes(data)
    if blob.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if blob.startswith(b"GIF87a") or blob.startswith(b"GIF89a"):
        return "image/gif"
    if blob.startswith(b"RIFF") and blob[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Нужна картинка JPEG, PNG, WebP или GIF")


def _http_url(raw: object) -> str:
    url = clean_text(raw, max_len=MAX_URL, allow_newlines=False)
    if not url:
        return ""
    if not URL_RE.match(url):
        raise ValueError("Ссылка должна начинаться с http:// или https://")
    return url


def normalize_stack(values: object) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("Стек — список строк")
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = clean_text(raw, max_len=MAX_STACK_ITEM, allow_newlines=False)
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    if len(out) > MAX_STACK:
        raise ValueError(f"Не больше {MAX_STACK} технологий")
    return out


def normalize_learn_slugs(values: object, *, allowed: set[str]) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("Выпуски Learn — список slug")
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        slug = clean_text(raw, max_len=128, allow_newlines=False).lower()
        if not slug:
            continue
        if not SLUG_RE.match(slug):
            raise ValueError("Некорректный slug Learn")
        if slug not in allowed:
            raise ValueError("К кейсу можно привязать только пройденный выпуск Learn")
        if slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    if len(out) > MAX_LEARN_SLUGS:
        raise ValueError(f"Не больше {MAX_LEARN_SLUGS} выпусков Learn на кейс")
    return out


def normalize_cert_track(raw: object, *, earned_ids: set[str]) -> str:
    track_id = clean_text(raw, max_len=32, allow_newlines=False).lower()
    if not track_id:
        return ""
    if track_id not in _TRACK_TITLES:
        raise ValueError("Неизвестный сезон сертификата")
    if track_id not in earned_ids:
        raise ValueError("Сертификат можно прикрепить только к закрытому сезону")
    return track_id


def cert_track_title(track_id: str) -> str:
    return _TRACK_TITLES.get(track_id, "")


def normalize_profile(body: dict[str, Any]) -> dict[str, Any]:
    return {
        "handle": normalize_handle(body.get("handle")),
        "headline": clean_text(body.get("headline"), max_len=MAX_HEADLINE, allow_newlines=False),
        "summary": clean_text(body.get("summary"), max_len=MAX_SUMMARY, allow_newlines=True),
        "is_published": bool(body.get("is_published")),
        "pinned_resume_id": parse_optional_uuid(body.get("pinned_resume_id")),
        "contact_phone": clean_text(body.get("contact_phone"), max_len=MAX_PHONE, allow_newlines=False),
        "contact_email": normalize_email(body.get("contact_email")),
        "contact_url": _http_url(body.get("contact_url")),
    }


def normalize_case(
    body: dict[str, Any],
    *,
    allowed_slugs: set[str],
    earned_ids: set[str],
) -> dict[str, Any]:
    title = clean_text(body.get("title"), max_len=MAX_TITLE, allow_newlines=False)
    if not title:
        raise ValueError("У кейса нужно название")
    return {
        "title": title,
        "role": clean_text(body.get("role"), max_len=MAX_ROLE, allow_newlines=False),
        "problem": clean_text(body.get("problem"), max_len=MAX_BODY, allow_newlines=True),
        "work": clean_text(body.get("work"), max_len=MAX_BODY, allow_newlines=True),
        "outcome": clean_text(body.get("outcome"), max_len=MAX_BODY, allow_newlines=True),
        "stack": normalize_stack(body.get("stack") or []),
        "repo_url": _http_url(body.get("repo_url")),
        "demo_url": _http_url(body.get("demo_url")),
        "learn_slugs": normalize_learn_slugs(body.get("learn_slugs") or [], allowed=allowed_slugs),
        "cert_track_id": normalize_cert_track(body.get("cert_track_id"), earned_ids=earned_ids),
        "blurb": clean_text(body.get("blurb"), max_len=MAX_BLURB, allow_newlines=False),
    }


def case_is_complete(case: dict[str, Any]) -> bool:
    if not str(case.get("title") or "").strip():
        return False
    if str(case.get("blurb") or "").strip():
        return True
    return bool(
        str(case.get("problem") or "").strip()
        and str(case.get("work") or "").strip()
        and str(case.get("outcome") or "").strip()
    )


def assert_publishable(*, headline: str, cases: list[dict[str, Any]]) -> None:
    if not str(headline or "").strip():
        raise ValueError("Для публикации нужен заголовок")
    if not cases:
        raise ValueError("Для публикации нужен хотя бы один кейс")
    missing = [str(case.get("title") or "кейс") for case in cases if not case_is_complete(case)]
    if missing:
        raise ValueError("Добавьте краткое описание: " + ", ".join(missing))


def track_id_for_episode(episode: str) -> Optional[str]:
    ep = (episode or "").strip().upper()
    if len(ep) > 1 and ep[0] == "B" and ep[1].isdigit():
        return "b"
    if ep.startswith("S01"):
        return "s01"
    if ep.startswith("PY"):
        return "py"
    if ep.startswith("QA"):
        return "qa"
    if ep.startswith("MAP"):
        return "map"
    return None


def quiz_pass_slugs(
    attempts: list[tuple[Any, ...]],
    *,
    threshold: int = CERT_QUIZ_PERCENT,
) -> set[str]:
    best: dict[str, int] = {}
    for row in attempts:
        key = str(row[0] or "")
        if not key.lower().startswith("learn/"):
            continue
        slug = key.split("/", 1)[1].strip().lower()
        total = int(row[2] or 0)
        if not slug or total <= 0:
            continue
        percent = round(int(row[1] or 0) / total * 100)
        previous = best.get(slug)
        if previous is None or percent > previous:
            best[slug] = percent
    return {slug for slug, percent in best.items() if percent >= threshold}


def cert_track_status(
    posts: list[dict[str, Any]],
    completed_slugs: set[str] | list[str],
    quiz_required: set[str] | None = None,
    quiz_passed: set[str] | None = None,
) -> list[dict[str, Any]]:
    completed = {str(slug).strip().lower() for slug in completed_slugs if str(slug).strip()}
    buckets: dict[str, list[str]] = {track_id: [] for track_id, _title in CERT_TRACKS}
    seen: dict[str, set[str]] = {track_id: set() for track_id, _title in CERT_TRACKS}
    for post in posts:
        track_id = track_id_for_episode(str(post.get("episode") or ""))
        slug = str(post.get("slug") or "").strip().lower()
        if not track_id or not slug or slug in seen[track_id]:
            continue
        seen[track_id].add(slug)
        buckets[track_id].append(slug)
    required = quiz_required or set()
    passed = quiz_passed or set()
    out: list[dict[str, Any]] = []
    for track_id, title in CERT_TRACKS:
        slugs = buckets[track_id]
        done = sum(1 for slug in slugs if slug in completed)
        needed = [slug for slug in slugs if slug in required] if quiz_required is not None else []
        quiz_ok = all(slug in passed for slug in needed)
        out.append(
            {
                "id": track_id,
                "title": title,
                "earned": bool(slugs) and done == len(slugs) and quiz_ok,
                "done": done,
                "total": len(slugs),
            }
        )
    return out


def collect_github_projects(project_lists: list[list[Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for projects in project_lists:
        if not isinstance(projects, list):
            continue
        for raw in projects:
            if not isinstance(raw, dict):
                continue
            name = clean_text(raw.get("name"), max_len=120, allow_newlines=False)
            url = clean_text(raw.get("url"), max_len=MAX_URL, allow_newlines=False)
            if not name or not url or not URL_RE.match(url):
                continue
            key = url.lower()
            item = {
                "name": name,
                "url": url,
                "description": clean_text(raw.get("description"), max_len=400, allow_newlines=False),
                "language": clean_text(raw.get("language"), max_len=64, allow_newlines=False),
                "selected": bool(raw.get("selected")),
            }
            prev = by_url.get(key)
            if prev is None:
                by_url[key] = item
                order.append(key)
                continue
            if item["selected"] and not prev["selected"]:
                by_url[key] = item
    selected = [by_url[key] for key in order if by_url[key]["selected"]]
    rest = [by_url[key] for key in order if not by_url[key]["selected"]]
    return (selected + rest)[:limit]


def display_name(first_name: str, last_name: str, username: str) -> str:
    full = clean_text(f"{first_name} {last_name}", max_len=160, allow_newlines=False)
    if full:
        return full
    fallback = clean_text(username, max_len=64, allow_newlines=False)
    return fallback or "Участник"


def excerpt_about(raw: object, *, limit: int = ABOUT_EXCERPT) -> str:
    text = clean_text(raw, max_len=8000, allow_newlines=True)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def validate_reorder(existing_ids: list[str], requested_ids: list[str]) -> None:
    if len(requested_ids) != len(existing_ids):
        raise ValueError("Передайте все кейсы в новом порядке")
    if len(set(requested_ids)) != len(requested_ids):
        raise ValueError("В порядке есть повтор")
    if set(requested_ids) != set(existing_ids):
        raise ValueError("В порядке есть неизвестный кейс")


def build_public_page(
    *,
    is_published: bool,
    handle: str,
    display: str,
    headline: str,
    summary: str,
    city: str,
    pinned: Optional[dict[str, Any]],
    cases: list[dict[str, Any]],
    contacts: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    if not is_published:
        return None
    source = contacts or {}
    return {
        "handle": handle,
        "displayName": display,
        "headline": headline,
        "summary": summary,
        "city": city,
        "pinnedResume": pinned,
        "contacts": {
            "phone": str(source.get("phone") or ""),
            "email": str(source.get("email") or ""),
            "url": str(source.get("url") or ""),
        },
        "cases": cases,
    }
