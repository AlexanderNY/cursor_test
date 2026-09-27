"""Публичные репозитории GitHub (без OAuth)."""
from __future__ import annotations

import re
from typing import Any

import httpx

GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
MAX_FETCH = 30
MAX_SELECTED = 6
USER_AGENT = "9to18-resume"


def normalize_github_username(raw: str) -> str:
    username = (raw or "").strip().lstrip("@")
    if not username or not GITHUB_USER_RE.match(username):
        raise ValueError("Некорректный GitHub username")
    return username


def parse_repo_payload(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("fork"):
            continue
        name = str(item.get("name") or "").strip()
        html_url = str(item.get("html_url") or "").strip()
        if not name or not html_url:
            continue
        out.append(
            {
                "name": name[:120],
                "url": html_url[:500],
                "description": str(item.get("description") or "").strip()[:400],
                "language": str(item.get("language") or "").strip()[:64],
                "stars": int(item.get("stargazers_count") or 0),
                "selected": False,
            }
        )
        if len(out) >= MAX_FETCH:
            break
    return out


def filter_selected_projects(
    projects: list[dict[str, Any]] | None,
    *,
    max_count: int = MAX_SELECTED,
) -> list[dict[str, Any]]:
    if not projects:
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in projects:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()[:120]
        url = str(raw.get("url") or "").strip()[:500]
        if not name or not url:
            continue
        key = url.lower()
        if key in seen:
            continue
        selected = bool(raw.get("selected"))
        if not selected and len([p for p in projects if isinstance(p, dict) and p.get("selected")]) > 0:
            # Keep unselected in stored list only if caller wants full list;
            # for PUT we store full list with selected flags, but export uses selected.
            pass
        seen.add(key)
        out.append(
            {
                "name": name,
                "url": url,
                "description": str(raw.get("description") or "").strip()[:400],
                "language": str(raw.get("language") or "").strip()[:64],
                "stars": int(raw.get("stars") or 0),
                "selected": selected,
            }
        )
    # Cap selected flags
    selected_count = 0
    for item in out:
        if item["selected"]:
            selected_count += 1
            if selected_count > max_count:
                item["selected"] = False
    return out


def selected_projects_only(
    projects: list[dict[str, Any]] | None,
    *,
    max_count: int = MAX_SELECTED,
) -> list[dict[str, Any]]:
    filtered = filter_selected_projects(projects, max_count=max_count)
    return [p for p in filtered if p.get("selected")][:max_count]


async def fetch_public_repos(username: str) -> list[dict[str, Any]]:
    user = normalize_github_username(username)
    url = f"https://api.github.com/users/{user}/repos"
    params = {"sort": "updated", "per_page": str(MAX_FETCH), "type": "owner"}
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, params=params, headers=headers)
    if resp.status_code == 404:
        raise LookupError("GitHub-пользователь не найден")
    if resp.status_code == 403:
        raise RuntimeError("GitHub API: лимит запросов, попробуйте позже")
    if resp.status_code >= 400:
        raise RuntimeError(f"GitHub API ошибка ({resp.status_code})")
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError("Неожиданный ответ GitHub API")
    return parse_repo_payload(data)
