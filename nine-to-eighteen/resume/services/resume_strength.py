"""Индикатор «силы резюме»: photo / about / релевантные модули Learn."""
from __future__ import annotations

from typing import Any, Optional

from services.resume_skills import BRANCH_SPECIALIZATION, SKILL_RULES, suggest_specialization

PHOTO_POINTS = 10
ABOUT_POINTS = 15
ABOUT_MIN_LEN = 40
LEARN_POINTS_PER_MODULE = 20
MAX_SCORE = 100


def _strength_weights() -> dict[str, int]:
    try:
        from services.runtime_settings import strength_override

        return strength_override()
    except Exception:
        return {
            "photoPoints": PHOTO_POINTS,
            "aboutPoints": ABOUT_POINTS,
            "aboutMinLen": ABOUT_MIN_LEN,
            "learnPointsPerModule": LEARN_POINTS_PER_MODULE,
            "maxScore": MAX_SCORE,
        }


def _branch_for_resume(
    specialization: str,
    completed_slugs: list[str] | set[str],
) -> Optional[str]:
    """Ветка карты, релевантная специальности резюме."""
    spec = (specialization or "").strip().lower()
    if spec:
        for branch, label in BRANCH_SPECIALIZATION.items():
            label_l = label.lower()
            if branch.lower() in spec or any(
                tok and len(tok) > 3 and tok in spec
                for tok in label_l.replace("/", " ").replace("-", " ").split()
            ):
                return branch
    suggested_label = suggest_specialization(completed_slugs)
    return _branch_key_from_label(suggested_label)


def _branch_key_from_label(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    for branch, text in BRANCH_SPECIALIZATION.items():
        if text == label:
            return branch
    return None


def relevant_learn_slugs(branch: Optional[str]) -> list[str]:
    """Slug’и Learn, релевантные ветке (или все skill-slug’и, если ветка неизвестна)."""
    slugs: list[str] = []
    seen: set[str] = set()
    for rule in SKILL_RULES:
        if branch and rule.map_branch != branch:
            continue
        for slug in rule.episode_slugs:
            if slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    return slugs


def compute_resume_strength(
    *,
    has_photo: bool,
    about: str,
    specialization: str = "",
    completed_slugs: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Счёт 0–100 + действия для недостающих баллов.

    +10 фото, +15 «О себе» (≥40 символов), +20 за каждый релевантный пройденный модуль Learn.
    """
    completed = {str(s).strip() for s in (completed_slugs or []) if str(s).strip()}
    branch = _branch_for_resume(specialization, completed)
    pool = relevant_learn_slugs(branch)
    done_relevant = [s for s in pool if s in completed]
    missing_relevant = [s for s in pool if s not in completed]

    weights = _strength_weights()
    photo_pts = int(weights.get("photoPoints", PHOTO_POINTS))
    about_pts = int(weights.get("aboutPoints", ABOUT_POINTS))
    about_min = int(weights.get("aboutMinLen", ABOUT_MIN_LEN))
    learn_pts = int(weights.get("learnPointsPerModule", LEARN_POINTS_PER_MODULE))
    max_score = int(weights.get("maxScore", MAX_SCORE))

    parts: list[dict[str, Any]] = []
    score = 0

    photo_ok = bool(has_photo)
    parts.append(
        {
            "id": "photo",
            "label": "Фото",
            "points": photo_pts if photo_ok else 0,
            "maxPoints": photo_pts,
            "done": photo_ok,
        }
    )
    if photo_ok:
        score += photo_pts

    about_text = (about or "").strip()
    about_ok = len(about_text) >= about_min
    parts.append(
        {
            "id": "about",
            "label": "О себе",
            "points": about_pts if about_ok else 0,
            "maxPoints": about_pts,
            "done": about_ok,
        }
    )
    if about_ok:
        score += about_pts

    learn_points = learn_pts * len(done_relevant)
    parts.append(
        {
            "id": "learn",
            "label": "Модули Learn",
            "points": learn_points,
            "maxPoints": learn_pts * max(len(pool), 1),
            "done": len(done_relevant) > 0,
            "doneCount": len(done_relevant),
            "totalRelevant": len(pool),
            "branch": branch,
        }
    )
    score += learn_points
    score = min(max_score, score)

    actions: list[dict[str, Any]] = []
    if not photo_ok:
        actions.append(
            {
                "id": "photo",
                "points": photo_pts,
                "title": f"Загрузите фото в кабинете (+{photo_pts}%)",
                "href": "/account",
            }
        )
    if not about_ok:
        actions.append(
            {
                "id": "about",
                "points": about_pts,
                "title": f"Заполните «О себе» (≥{about_min} символов, +{about_pts}%)",
                "href": None,
            }
        )
    for slug in missing_relevant[:5]:
        rule_name = next(
            (r.name for r in SKILL_RULES if slug in r.episode_slugs),
            slug,
        )
        actions.append(
            {
                "id": f"learn:{slug}",
                "points": learn_pts,
                "title": f"Пройдите модуль «{rule_name}» ({slug}), чтобы получить +{learn_pts}%",
                "href": f"/game/learn/{slug}",
                "slug": slug,
            }
        )

    return {
        "score": score,
        "maxScore": max_score,
        "parts": parts,
        "actions": actions,
        "relevantBranch": branch,
        "doneRelevantSlugs": done_relevant,
        "missingRelevantSlugs": missing_relevant,
    }
