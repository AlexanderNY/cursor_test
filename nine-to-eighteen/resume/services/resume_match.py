"""Match Score: пересечение навыков резюме с текстом вакансии."""
from __future__ import annotations

import logging
from typing import Any

from services.resume_skills import SKILL_RULES
from services.resume_source import detect_skill_keys_in_text

logger = logging.getLogger(__name__)


def _skill_keys_from_resume(
    *,
    selected_keys: list[str],
    generated_skills: list[dict[str, Any]] | list[Any],
    about: str,
    source_text: str,
) -> set[str]:
    keys: set[str] = set()
    for raw in selected_keys or []:
        key = str(raw or "").strip()
        if key:
            keys.add(key)
    for skill in generated_skills or []:
        if isinstance(skill, dict):
            key = str(skill.get("key") or "").strip()
            if key:
                keys.add(key)
    keys |= detect_skill_keys_in_text(about or "")
    keys |= detect_skill_keys_in_text(source_text or "")
    return keys


def compute_match_score(
    *,
    vacancy_text: str,
    selected_keys: list[str],
    generated_skills: list[dict[str, Any]] | list[Any],
    about: str = "",
    source_text: str = "",
) -> dict[str, Any]:
    """Rule-based match: required keys from vacancy aliases vs resume evidence."""
    vacancy = (vacancy_text or "").strip()
    required = detect_skill_keys_in_text(vacancy)
    resume_keys = _skill_keys_from_resume(
        selected_keys=selected_keys,
        generated_skills=generated_skills,
        about=about,
        source_text=source_text,
    )

    if not required:
        # No known skill tokens in vacancy — score by soft presence of any resume skills.
        score = 50 if resume_keys else 0
        return {
            "score": score,
            "matchedKeys": sorted(resume_keys),
            "missingKeys": [],
            "requiredKeys": [],
            "summary": (
                "В тексте вакансии не нашлось известных технологий из каталога. "
                "Оценка ориентировочная — добавьте ключевые требования (Python, FastAPI и т.д.)."
            ),
        }

    matched = sorted(required & resume_keys)
    missing = sorted(required - resume_keys)
    score = int(round(100 * len(matched) / max(len(required), 1)))
    score = max(0, min(100, score))

    name_by_key = {r.key: r.name for r in SKILL_RULES}
    matched_names = [name_by_key.get(k, k) for k in matched]
    missing_names = [name_by_key.get(k, k) for k in missing]

    if score >= 80:
        summary = (
            f"Сильное совпадение ({score}%): есть {', '.join(matched_names) or '—'}. "
            + (f"Стоит закрыть: {', '.join(missing_names)}." if missing_names else "")
        ).strip()
    elif score >= 50:
        summary = (
            f"Частичное совпадение ({score}%). Есть: {', '.join(matched_names) or 'нет'}. "
            f"Не хватает: {', '.join(missing_names) or '—'}."
        )
    else:
        summary = (
            f"Слабое совпадение ({score}%). В вакансии ждут: "
            f"{', '.join(name_by_key.get(k, k) for k in sorted(required))}. "
            f"В резюме пока есть пересечение по: {', '.join(matched_names) or 'ничему'}."
        )

    return {
        "score": score,
        "matchedKeys": matched,
        "missingKeys": missing,
        "requiredKeys": sorted(required),
        "summary": summary,
    }


async def enrich_match_summary(
    base: dict[str, Any],
    *,
    vacancy_text: str,
    specialization: str,
) -> dict[str, Any]:
    """Optional 1–2 sentence AI polish; keeps rule-based score/keys."""
    out = dict(base)
    try:
        from shared import ai_client

        if not await ai_client.is_ready():
            return out
        prompt = (
            f"Должность: {specialization or 'не указана'}\n"
            f"Score: {base.get('score')}\n"
            f"Совпали: {', '.join(base.get('matchedKeys') or []) or 'нет'}\n"
            f"Не хватает: {', '.join(base.get('missingKeys') or []) or 'нет'}\n"
            f"Вакансия (фрагмент):\n{(vacancy_text or '')[:1500]}\n\n"
            "Напиши 1–2 предложения по-русски: насколько резюме подходит и на что сделать упор. "
            "Без списков и markdown."
        )
        text = await ai_client.complete(
            prompt,
            system="Ты карьерный консультант. Кратко и конкретно.",
            max_tokens=200,
        )
        polished = (text or "").strip()
        if polished:
            out["summary"] = polished[:600]
    except Exception:
        logger.exception("match-score AI summary failed; keeping rule summary")
    return out
