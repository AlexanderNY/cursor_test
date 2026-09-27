"""Бейджи резюме: Learn-сезоны + quiz attempts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.resume_skills import SKILL_RULES

QUIZ_PASS_RATIO = 0.7
QUIZ_MIN_TOTAL = 3
MAX_SELECTED_BADGES = 8


@dataclass(frozen=True)
class LearnSeasonBadge:
    id: str
    title: str
    description: str
    slug_prefixes: tuple[str, ...]


LEARN_SEASON_DEFS: tuple[LearnSeasonBadge, ...] = (
    LearnSeasonBadge(
        id="learn_season_b",
        title="Сезон B · Первое приложение",
        description="Закрыты выпуски сезона B (Git → Python → React → Docker).",
        slug_prefixes=("b",),
    ),
    LearnSeasonBadge(
        id="learn_season_s01",
        title="Сезон 1 · Слои и стенд",
        description="Закрыты выпуски S01 (заявки, Postgres, Compose).",
        slug_prefixes=("s01",),
    ),
    LearnSeasonBadge(
        id="learn_season_map",
        title="Карта · листья собеса",
        description="Закрыты map-выпуски, привязанные к learning-map.",
        slug_prefixes=("map-",),
    ),
)

QUIZ_COUNT_THRESHOLDS: tuple[tuple[str, int, str], ...] = (
    ("quiz_count_1", 1, "Зачтён 1 квиз (≥70%)"),
    ("quiz_count_3", 3, "Зачтено 3 квиза (≥70%)"),
    ("quiz_count_5", 5, "Зачтено 5 квизов (≥70%)"),
)


def _slug_matches_prefix(slug: str, prefix: str) -> bool:
    s = slug.lower()
    p = prefix.lower()
    if p == "b":
        return len(s) > 1 and s[0] == "b" and s[1].isdigit()
    if p == "s01":
        return s.startswith("s01")
    return s.startswith(p)


def _slugs_for_prefixes(prefixes: tuple[str, ...]) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    for rule in SKILL_RULES:
        for slug in rule.episode_slugs:
            s = str(slug).strip().lower()
            if not s or s in seen:
                continue
            if any(_slug_matches_prefix(s, prefix) for prefix in prefixes):
                seen.add(s)
                found.append(s)
    return tuple(found)


def learn_season_required_slugs(badge_id: str) -> tuple[str, ...]:
    for season in LEARN_SEASON_DEFS:
        if season.id == badge_id:
            return _slugs_for_prefixes(season.slug_prefixes)
    return ()


def _best_quiz_by_source(
    attempts: list[dict[str, Any]],
) -> dict[str, tuple[int, int]]:
    """source_key -> (best_score, total) with highest score/total ratio."""
    best: dict[str, tuple[int, int, float]] = {}
    for row in attempts:
        source = str(row.get("source_key") or row.get("sourceKey") or "").strip()
        if not source:
            continue
        try:
            score = int(row.get("score") or 0)
            total = int(row.get("total") or 0)
        except (TypeError, ValueError):
            continue
        if total <= 0:
            continue
        ratio = score / total
        prev = best.get(source)
        if prev is None or ratio > prev[2] or (ratio == prev[2] and score > prev[0]):
            best[source] = (score, total, ratio)
    return {k: (v[0], v[1]) for k, v in best.items()}


def is_quiz_passed(score: int, total: int) -> bool:
    if total < QUIZ_MIN_TOTAL:
        return False
    return (score / total) >= QUIZ_PASS_RATIO


def compute_badges(
    *,
    completed_slugs: list[str] | set[str],
    quiz_attempts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    completed = {str(s).strip().lower() for s in completed_slugs if str(s).strip()}
    out: list[dict[str, Any]] = []

    for season in LEARN_SEASON_DEFS:
        required = _slugs_for_prefixes(season.slug_prefixes)
        if not required:
            continue
        done = sum(1 for s in required if s in completed)
        earned = done >= len(required) and len(required) > 0
        out.append(
            {
                "id": season.id,
                "title": season.title,
                "description": season.description,
                "kind": "learn",
                "earned": earned,
                "progress": {"done": done, "total": len(required)},
            }
        )

    best = _best_quiz_by_source(quiz_attempts)
    passed_sources = [
        src for src, (score, total) in best.items() if is_quiz_passed(score, total)
    ]
    passed_count = len(passed_sources)

    for badge_id, threshold, title in QUIZ_COUNT_THRESHOLDS:
        out.append(
            {
                "id": badge_id,
                "title": title,
                "description": f"Лучшие попытки квизов с результатом ≥{int(QUIZ_PASS_RATIO * 100)}%.",
                "kind": "quiz",
                "earned": passed_count >= threshold,
                "progress": {"done": min(passed_count, threshold), "total": threshold},
            }
        )

    for source in sorted(passed_sources)[:20]:
        score, total = best[source]
        safe_id = "quiz_src_" + "".join(
            ch if ch.isalnum() or ch in "-_" else "_" for ch in source
        )[:80]
        out.append(
            {
                "id": safe_id,
                "title": f"Квиз: {source}",
                "description": f"Лучший результат {score}/{total}",
                "kind": "quiz",
                "earned": True,
                "progress": {"done": score, "total": total},
                "sourceKey": source,
            }
        )

    return out


def filter_selected_badge_ids(
    selected: list[str] | None,
    *,
    earned_ids: set[str],
    max_count: int = MAX_SELECTED_BADGES,
) -> list[str]:
    if not selected:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in selected:
        badge_id = str(raw or "").strip()
        if not badge_id or badge_id in seen or badge_id not in earned_ids:
            continue
        seen.add(badge_id)
        out.append(badge_id)
        if len(out) >= max_count:
            break
    return out
