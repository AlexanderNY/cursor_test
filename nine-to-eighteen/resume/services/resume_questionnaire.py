"""Опросник «идеальное резюме» и наполнение шаблона по ответам.

Без LLM: детерминированные формулировки под HH-стиль.
"""
from __future__ import annotations

from typing import Any, Optional


QuestionOption = dict[str, str]
QuestionDef = dict[str, Any]


QUESTIONNAIRE: list[QuestionDef] = [
    {
        "id": "role_track",
        "type": "single",
        "required": True,
        "title": "Какую роль хотите видеть в резюме?",
        "hint": "От этого зависят должность и формулировки «о себе».",
        "options": [
            {"id": "backend", "label": "Backend-разработчик"},
            {"id": "frontend", "label": "Frontend-разработчик"},
            {"id": "fullstack", "label": "Fullstack-разработчик"},
            {"id": "devops", "label": "DevOps / Infrastructure"},
            {"id": "qa", "label": "QA / тестирование"},
            {"id": "analyst", "label": "Системный / бизнес-аналитик"},
            {"id": "product", "label": "Product / PO"},
            {"id": "data", "label": "Данные / SQL"},
            {"id": "general", "label": "Пока выбираю направление"},
        ],
    },
    {
        "id": "experience_level",
        "type": "single",
        "required": True,
        "title": "Какой уровень опыта укажем?",
        "hint": "Честная самооценка — лучше для собеседования.",
        "options": [
            {"id": "student", "label": "Учусь / первые пет-проекты"},
            {"id": "junior", "label": "Junior (есть учебные или небольшие проекты)"},
            {"id": "middle", "label": "Middle (уверенно веду учебный стенд / pet end-to-end)"},
        ],
    },
    {
        "id": "goal",
        "type": "single",
        "required": True,
        "title": "Какая цель резюме?",
        "options": [
            {"id": "first_job", "label": "Первая работа в IT"},
            {"id": "internship", "label": "Стажировка"},
            {"id": "switch", "label": "Смена направления / стека"},
            {"id": "strengthen", "label": "Усилить текущий профиль"},
        ],
    },
    {
        "id": "employment",
        "type": "multi",
        "required": True,
        "title": "Какой тип занятости рассматриваете?",
        "options": [
            {"id": "full", "label": "Полная занятость"},
            {"id": "part", "label": "Частичная занятость"},
            {"id": "project", "label": "Проектная работа"},
            {"id": "internship", "label": "Стажировка"},
            {"id": "volunteer", "label": "Волонтёрство / open source"},
        ],
    },
    {
        "id": "work_formats",
        "type": "multi",
        "required": True,
        "title": "Формат работы",
        "options": [
            {"id": "office", "label": "Офис"},
            {"id": "remote", "label": "Удалённо"},
            {"id": "hybrid", "label": "Гибрид"},
            {"id": "travel", "label": "Разъездная"},
        ],
    },
    {
        "id": "salary_band",
        "type": "single",
        "required": True,
        "title": "Желаемый оклад (₽ на руки, ориентир)",
        "options": [
            {"id": "open", "label": "По договорённости"},
            {"id": "up_80", "label": "до 80 000"},
            {"id": "80_120", "label": "80–120 000"},
            {"id": "120_180", "label": "120–180 000"},
            {"id": "180_250", "label": "180–250 000"},
            {"id": "250_plus", "label": "от 250 000"},
        ],
    },
    {
        "id": "strengths",
        "type": "multi",
        "required": True,
        "title": "Что подчеркнуть в «о себе»?",
        "hint": "Можно несколько пунктов — они попадут в текст.",
        "options": [
            {"id": "learning", "label": "Быстро учусь по практике"},
            {"id": "pet", "label": "Есть pet / учебный проект end-to-end"},
            {"id": "docs", "label": "Люблю ясный контракт и документацию"},
            {"id": "debug", "label": "Сильная сторона — отладка и разбор инцидентов"},
            {"id": "team", "label": "Комфортно в команде и код-ревью"},
            {"id": "product", "label": "Думаю о пользе для пользователя"},
            {"id": "quality", "label": "Внимателен к качеству и регрессиям"},
            {"id": "ops", "label": "Интересует деплой и эксплуатация"},
        ],
    },
    {
        "id": "tone",
        "type": "single",
        "required": True,
        "title": "Стиль блока «о себе»",
        "options": [
            {"id": "concise", "label": "Коротко (3–4 предложения)"},
            {"id": "balanced", "label": "Сбалансировано"},
            {"id": "detailed", "label": "Подробнее (с акцентом на путь обучения)"},
        ],
    },
    {
        "id": "extra",
        "type": "text",
        "required": False,
        "title": "Что ещё важно добавить своими словами?",
        "hint": "Опционально: одна-две фразы — вставим в конец «о себе».",
        "maxLength": 500,
        "placeholder": "Например: ищу команду с менторством и code review…",
    },
]

ROLE_SPECIALIZATION: dict[str, dict[str, str]] = {
    "backend": {
        "student": "Junior Backend-разработчик (Python)",
        "junior": "Backend-разработчик (Python / FastAPI)",
        "middle": "Backend-разработчик (Python, API, PostgreSQL)",
    },
    "frontend": {
        "student": "Junior Frontend-разработчик (React)",
        "junior": "Frontend-разработчик (React)",
        "middle": "Frontend-разработчик (React, UI/API)",
    },
    "fullstack": {
        "student": "Junior Fullstack-разработчик",
        "junior": "Fullstack-разработчик (Python + React)",
        "middle": "Fullstack-разработчик (API + UI + деплой)",
    },
    "devops": {
        "student": "Junior DevOps / Infrastructure",
        "junior": "DevOps-инженер (Docker / CI)",
        "middle": "DevOps-инженер (Docker, Compose, основы k8s)",
    },
    "qa": {
        "student": "Junior QA-инженер",
        "junior": "QA-инженер (ручное + API)",
        "middle": "QA-инженер (тест-дизайн, API, регрессии)",
    },
    "analyst": {
        "student": "Junior системный аналитик",
        "junior": "Системный аналитик",
        "middle": "Системный аналитик (требования, интеграции)",
    },
    "product": {
        "student": "Junior Product / PO",
        "junior": "Product Owner / Product Manager",
        "middle": "Product Manager (бэклог, приоритизация)",
    },
    "data": {
        "student": "Junior SQL / данные",
        "junior": "Инженер данных / SQL-разработчик",
        "middle": "Инженер данных (SQL, моделирование)",
    },
    "general": {
        "student": "Стажёр / Junior IT",
        "junior": "Junior-специалист (обучение 9to18)",
        "middle": "Специалист (учебный путь 9to18)",
    },
}

SALARY_MIDPOINTS: dict[str, Optional[int]] = {
    "open": None,
    "up_80": 70_000,
    "80_120": 100_000,
    "120_180": 150_000,
    "180_250": 210_000,
    "250_plus": 280_000,
}

GOAL_PHRASES: dict[str, str] = {
    "first_job": "Ищу первую роль в IT с понятными задачами и обратной связью.",
    "internship": "Открыт(а) к стажировке: готов(а) быстро включаться в учебный и рабочий ритм.",
    "switch": "Перехожу в выбранное направление и собираю профиль через практику и Learn.",
    "strengthen": "Усиливаю текущий профиль практикой на учебном стенде и разборами в Learn.",
}

STRENGTH_PHRASES: dict[str, str] = {
    "learning": "быстро осваиваю инструменты на практике",
    "pet": "собираю учебные / pet-проекты end-to-end",
    "docs": "ценю ясный API-контракт и документацию",
    "debug": "спокойно разбираю ошибки и логи",
    "team": "удобно работаю в команде и обсуждаю решения",
    "product": "держу в фокусе пользу для пользователя",
    "quality": "внимателен(на) к регрессиям и качеству",
    "ops": "интересны деплой и эксплуатация сервисов",
}

LEVEL_OPENERS: dict[str, str] = {
    "student": "Сейчас активно учусь и собираю портфель практических задач.",
    "junior": "Есть учебный и/или небольшой практический опыт — готов(а) расти в команде.",
    "middle": "Уверенно веду учебный стенд от API до UI/деплоя и могу объяснить решения.",
}

EMPLOYMENT_ALLOWED = {"full", "part", "project", "volunteer", "internship"}
WORK_FORMAT_ALLOWED = {"office", "remote", "hybrid", "travel"}


def get_questionnaire() -> dict[str, Any]:
    return {
        "version": 1,
        "title": "Соберите идеальное резюме",
        "lead": (
            "Короткий опрос: по ответам заполним должность, оклад, занятость и текст «о себе». "
            "Потом можно всё поправить вручную и добавить навыки из Learn."
        ),
        "questions": QUESTIONNAIRE,
    }


def _single(answers: dict[str, Any], key: str) -> str:
    raw = answers.get(key)
    if isinstance(raw, list):
        return str(raw[0]).strip() if raw else ""
    return str(raw or "").strip()


def _multi(answers: dict[str, Any], key: str) -> list[str]:
    raw = answers.get(key)
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            value = str(item or "").strip()
            if value and value not in out:
                out.append(value)
        return out
    return []


def validate_answers(answers: dict[str, Any]) -> list[str]:
    """Возвращает список ошибок валидации (пустой = ok)."""
    errors: list[str] = []
    by_id = {q["id"]: q for q in QUESTIONNAIRE}
    for question in QUESTIONNAIRE:
        qid = str(question["id"])
        qtype = str(question["type"])
        required = bool(question.get("required"))
        if qtype == "text":
            text = str(answers.get(qid) or "").strip()
            max_len = int(question.get("maxLength") or 500)
            if required and not text:
                errors.append(f"Заполните: {question['title']}")
            elif len(text) > max_len:
                errors.append(f"Слишком длинный ответ: {question['title']}")
            continue

        allowed = {str(o["id"]) for o in question.get("options") or []}
        if qtype == "single":
            value = _single(answers, qid)
            if required and not value:
                errors.append(f"Выберите вариант: {question['title']}")
            elif value and value not in allowed:
                errors.append(f"Некорректный ответ: {qid}")
        elif qtype == "multi":
            values = _multi(answers, qid)
            if required and not values:
                errors.append(f"Выберите хотя бы один вариант: {question['title']}")
            elif any(v not in allowed for v in values):
                errors.append(f"Некорректный ответ: {qid}")
    # ignore unknown keys quietly
    _ = by_id
    return errors


def _join_ru(parts: list[str]) -> str:
    clean = [p for p in parts if p]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} и {clean[1]}"
    return ", ".join(clean[:-1]) + f" и {clean[-1]}"


def build_about(answers: dict[str, Any], *, branch_hints: Optional[list[str]] = None) -> str:
    level = _single(answers, "experience_level") or "junior"
    goal = _single(answers, "goal") or "first_job"
    tone = _single(answers, "tone") or "balanced"
    strengths = _multi(answers, "strengths")
    extra = str(answers.get("extra") or "").strip()

    opener = LEVEL_OPENERS.get(level, LEVEL_OPENERS["junior"])
    goal_line = GOAL_PHRASES.get(goal, GOAL_PHRASES["first_job"])
    strength_bits = [STRENGTH_PHRASES[s] for s in strengths if s in STRENGTH_PHRASES]
    strength_line = (
        f"В работе опираюсь на то, что {_join_ru(strength_bits)}."
        if strength_bits
        else ""
    )

    learn_line = ""
    if branch_hints:
        learn_line = (
            "По карте обучения закрыты направления: "
            + ", ".join(h.replace("ветка карты: ", "") for h in branch_hints[:4])
            + "."
        )

    if tone == "concise":
        parts = [opener, goal_line]
        if strength_bits:
            parts.append(f"Сильные стороны: {_join_ru(strength_bits)}.")
        if extra:
            parts.append(extra)
        return " ".join(p for p in parts if p)

    if tone == "detailed":
        parts = [
            opener,
            goal_line,
            strength_line,
            "Резюме опирается на практику в Learn 9to18: статьи, отмеченный прогресс и учебный стенд.",
            learn_line,
            extra,
        ]
        return " ".join(p for p in parts if p)

    # balanced
    parts = [opener, goal_line, strength_line, learn_line, extra]
    return " ".join(p for p in parts if p)


def apply_questionnaire_to_template(
    answers: dict[str, Any],
    *,
    branch_hints: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Собирает поля резюме из ответов опросника."""
    role = _single(answers, "role_track") or "general"
    level = _single(answers, "experience_level") or "junior"
    specialization = ROLE_SPECIALIZATION.get(role, ROLE_SPECIALIZATION["general"]).get(
        level,
        ROLE_SPECIALIZATION["general"]["junior"],
    )
    employment = [
        e for e in _multi(answers, "employment") if e in EMPLOYMENT_ALLOWED
    ]
    work_formats = [
        w for w in _multi(answers, "work_formats") if w in WORK_FORMAT_ALLOWED
    ]
    salary_band = _single(answers, "salary_band") or "open"
    salary_amount = SALARY_MIDPOINTS.get(salary_band)

    title = f"Резюме · {specialization}"
    about = build_about(answers, branch_hints=branch_hints)

    return {
        "title": title[:255],
        "specialization": specialization[:255],
        "salaryAmount": salary_amount,
        "salaryCurrency": "RUB",
        "employmentTypes": employment,
        "workFormats": work_formats,
        "about": about[:8000],
    }
