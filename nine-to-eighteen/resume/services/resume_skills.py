"""Правила обогащения навыков резюме из прогресса Learn / карты обучения.

Каталог зеркалит ветки map-learn-links.ts (одинаковые episode slug).
Без LLM: junior при 1 завершённом slug навыка, middle при ≥2.
Docker: оба b10-docker и b11-compose → middle с формулировкой про Dockerfile/compose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class SkillRule:
    key: str
    name: str
    episode_slugs: tuple[str, ...]
    junior_evidence: str
    middle_evidence: str
    map_branch: str = ""


SKILL_RULES: tuple[SkillRule, ...] = (
    SkillRule(
        key="docker",
        name="Docker",
        episode_slugs=("b10-docker", "b11-compose"),
        junior_evidence="знакомство с Docker / образами",
        middle_evidence="pet project, опыт формирования Dockerfile и docker-compose",
        map_branch="devops",
    ),
    SkillRule(
        key="kubernetes",
        name="Kubernetes",
        episode_slugs=("map-k8s",),
        junior_evidence="основы оркестрации и манифестов",
        middle_evidence="деплой учебных стендов в k8s",
        map_branch="devops",
    ),
    SkillRule(
        key="cicd",
        name="CI/CD",
        episode_slugs=("map-cicd",),
        junior_evidence="пайплайны сборки и деплоя",
        middle_evidence="настройка CI для pet project",
        map_branch="devops",
    ),
    SkillRule(
        key="networking",
        name="Сети",
        episode_slugs=("map-networking",),
        junior_evidence="базовые сетевые понятия для сервисов",
        middle_evidence="сетевая схема учебного стенда",
        map_branch="devops",
    ),
    SkillRule(
        key="python",
        name="Python",
        episode_slugs=("b03-python", "b07-notes-api", "s01e05-fastapi"),
        junior_evidence="синтаксис и учебные скрипты",
        middle_evidence="сервисы и API на Python",
        map_branch="разработка",
    ),
    SkillRule(
        key="fastapi",
        name="FastAPI",
        episode_slugs=("b04-fastapi-health", "s01e05-fastapi", "b07-notes-api"),
        junior_evidence="health-check и роуты",
        middle_evidence="REST API и валидация запросов",
        map_branch="разработка",
    ),
    SkillRule(
        key="react",
        name="React",
        episode_slugs=("b08-react-list", "b09-react-form", "s01e10-react"),
        junior_evidence="компоненты и списки",
        middle_evidence="формы и клиентский UI",
        map_branch="разработка",
    ),
    SkillRule(
        key="architecture",
        name="Архитектура",
        episode_slugs=("s01e01-sloi", "s01e02-karta", "b01-karta", "b12-sklejka"),
        junior_evidence="слои и карта сервисов",
        middle_evidence="склейка учебного стенда end-to-end",
        map_branch="разработка",
    ),
    SkillRule(
        key="postgresql",
        name="PostgreSQL",
        episode_slugs=("s01e07-postgres", "s01e08-sql", "map-normalization", "map-sql-nosql"),
        junior_evidence="SQL и моделирование",
        middle_evidence="нормализация и работа с БД сервиса",
        map_branch="данные",
    ),
    SkillRule(
        key="redis",
        name="Redis",
        episode_slugs=("map-redis",),
        junior_evidence="кэш и ключ-значение",
        middle_evidence="кэширование в учебном стенде",
        map_branch="данные",
    ),
    SkillRule(
        key="git",
        name="Git",
        episode_slugs=("s01e03-git", "b02-git", "b06-git-branch"),
        junior_evidence="коммиты и ветки",
        middle_evidence="ветвление и совместная работа",
        map_branch="инструменты",
    ),
    SkillRule(
        key="api_test",
        name="API-тестирование",
        episode_slugs=("s01e06-insomnia", "b05-api-check"),
        junior_evidence="проверка HTTP API",
        middle_evidence="сценарии проверки эндпоинтов",
        map_branch="инструменты",
    ),
    SkillRule(
        key="regex",
        name="Regex",
        episode_slugs=("s01e09-regex",),
        junior_evidence="базовые регулярные выражения",
        middle_evidence="парсинг и валидация строк",
        map_branch="инструменты",
    ),
    SkillRule(
        key="security",
        name="Безопасность",
        episode_slugs=("map-auth-jwt", "map-https-access"),
        junior_evidence="JWT и HTTPS",
        middle_evidence="разграничение доступа в сервисах",
        map_branch="безопасность",
    ),
    SkillRule(
        key="qa",
        name="Тестирование",
        episode_slugs=("map-qa", "map-e2e"),
        junior_evidence="тест-дизайн",
        middle_evidence="E2E и проверка сценариев",
        map_branch="тестирование",
    ),
    SkillRule(
        key="product",
        name="Аналитика и продукт",
        episode_slugs=("s01e04-sa", "map-requirements", "map-product-backlog"),
        junior_evidence="требования и SA",
        middle_evidence="бэклог и приоритизация",
        map_branch="аналитика и продукт",
    ),
    SkillRule(
        key="soft_skills",
        name="Soft skills",
        episode_slugs=("map-soft-skills",),
        junior_evidence="подготовка к поведенческим вопросам",
        middle_evidence="структурированные ответы на интервью",
        map_branch="soft skills",
    ),
)

BRANCH_HINT_RATIO = 0.6

BRANCH_SPECIALIZATION: dict[str, str] = {
    "разработка": "Backend / Fullstack-разработчик",
    "devops": "DevOps-инженер",
    "данные": "Инженер данных / SQL-разработчик",
    "аналитика и продукт": "Системный аналитик",
    "тестирование": "QA-инженер",
    "безопасность": "Специалист по безопасности приложений",
    "инструменты": "Инженер сопровождения / Tools",
    "soft skills": "Специалист (soft skills)",
}


def _completed_for_rule(rule: SkillRule, completed: set[str]) -> list[str]:
    return [slug for slug in rule.episode_slugs if slug in completed]


def skill_level_and_evidence(
    rule: SkillRule,
    matched_slugs: list[str],
) -> tuple[str, str]:
    if not matched_slugs:
        return "junior", rule.junior_evidence

    if rule.key == "docker":
        has_docker = "b10-docker" in matched_slugs
        has_compose = "b11-compose" in matched_slugs
        if has_docker and has_compose:
            return "middle", rule.middle_evidence
        return "junior", rule.junior_evidence

    if len(matched_slugs) >= 2:
        return "middle", rule.middle_evidence
    return "junior", rule.junior_evidence


def generate_skills_from_progress(
    completed_slugs: list[str] | set[str],
    *,
    selected_keys: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    completed = {str(s).strip() for s in completed_slugs if str(s).strip()}
    skills: list[dict[str, Any]] = []
    for rule in SKILL_RULES:
        matched = _completed_for_rule(rule, completed)
        if not matched:
            continue
        level, evidence = skill_level_and_evidence(rule, matched)
        skills.append(
            {
                "key": rule.key,
                "name": rule.name,
                "level": level,
                "evidence": evidence,
                "sourceSlugs": matched,
                "mapBranch": rule.map_branch or None,
                "display": f"{rule.name} — {level} ({evidence})",
            }
        )

    if selected_keys is not None:
        allow = {k.strip() for k in selected_keys if k and str(k).strip()}
        skills = [s for s in skills if s["key"] in allow]

    return skills


def branch_completion_hints(completed_slugs: list[str] | set[str]) -> list[str]:
    completed = {str(s).strip() for s in completed_slugs if str(s).strip()}
    by_branch: dict[str, list[str]] = {}
    for rule in SKILL_RULES:
        if not rule.map_branch:
            continue
        by_branch.setdefault(rule.map_branch, [])
        for slug in rule.episode_slugs:
            if slug not in by_branch[rule.map_branch]:
                by_branch[rule.map_branch].append(slug)

    hints: list[str] = []
    for branch, slugs in by_branch.items():
        if not slugs:
            continue
        done = sum(1 for s in slugs if s in completed)
        if done / len(slugs) >= BRANCH_HINT_RATIO:
            label = branch[0].upper() + branch[1:] if branch else branch
            hints.append(f"ветка карты: {label}")
    return hints


def suggest_specialization(completed_slugs: list[str] | set[str]) -> Optional[str]:
    completed = {str(s).strip() for s in completed_slugs if str(s).strip()}
    scores: dict[str, int] = {}
    for rule in SKILL_RULES:
        if not rule.map_branch:
            continue
        matched = len(_completed_for_rule(rule, completed))
        if matched:
            scores[rule.map_branch] = scores.get(rule.map_branch, 0) + matched
    if not scores:
        return None
    best = max(scores.items(), key=lambda item: item[1])[0]
    return BRANCH_SPECIALIZATION.get(best)


def missing_slugs_for_upgrade(skill_key: str, completed_slugs: list[str] | set[str]) -> list[str]:
    completed = {str(s).strip() for s in completed_slugs if str(s).strip()}
    rule = next((r for r in SKILL_RULES if r.key == skill_key), None)
    if rule is None:
        return []
    matched = _completed_for_rule(rule, completed)
    if not matched:
        return list(rule.episode_slugs)
    level, _ = skill_level_and_evidence(rule, matched)
    if level == "middle":
        return []
    return [s for s in rule.episode_slugs if s not in completed]
