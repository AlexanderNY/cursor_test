#!/usr/bin/env python3
"""Append map-* Learn articles for learning-map leaves into learn_seed.json."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "data" / "learn_seed.json"
START = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)


def article(
    *,
    n: int,
    slug: str,
    title: str,
    short: str,
    rubric: str,
    intro: str,
    sections: list[dict[str, str]],
    anki: list[dict[str, str]],
    summary: list[str],
    quiz: list[dict[str, str]] | None = None,
    diagrams: list[dict[str, str]] | None = None,
    lab: str = "",
) -> dict:
    structured = {
        "version": 1,
        "intro": intro.strip(),
        "sections": sections,
        "diagrams": diagrams or [],
        "quiz": quiz
        or [
            {
                "question": f"Одной фразой: о чём статья «{short}»?",
                "answer": short,
                "explain": title,
            }
        ],
        "anki": anki,
        "summary": summary,
    }
    theory_parts = [intro.strip()]
    for section in sections:
        if section.get("heading"):
            theory_parts.append(f"## {section['heading']}")
        if section.get("body"):
            theory_parts.append(section["body"])
    return {
        "slug": slug,
        "episode": f"MAP{n:02d}",
        "title": title,
        "shortTitle": short,
        "rubricId": rubric,
        "order": 200 + n,
        "theory": "\n\n".join(theory_parts),
        "lab": lab.strip(),
        "cheatsheet": "\n".join(f"- {line}" for line in summary),
        "diagram": (diagrams or [{}])[0].get("mermaid", "") if diagrams else "",
        "links": [],
        "structured": structured,
        "theoryFormat": "markdown",
        "labFormat": "markdown",
        "cheatsheetFormat": "markdown",
        "publishedAt": (START + timedelta(days=n - 1)).isoformat().replace("+00:00", "Z"),
    }


ARTICLES = [
    article(
        n=1,
        slug="map-requirements",
        title="Требования и user stories",
        short="Требования",
        rubric="api",
        intro=(
            "На собеседовании аналитика и PO ждут ясности: кто пользователь, какая цель, "
            "как понять что готово. User story — формат, а не магия."
        ),
        sections=[
            {
                "heading": "INVEST и критерии",
                "body": (
                    "Хорошая история: Independent, Negotiable, Valuable, Estimable, Small, Testable.\n\n"
                    "Acceptance criteria отвечают на «как проверить». Без них история — пожелание."
                ),
            },
            {
                "heading": "Анти-паттерны",
                "body": (
                    "- «Сделать удобно» без сценария\n"
                    "- Техническое решение вместо ценности\n"
                    "- Критерии только для happy path"
                ),
            },
        ],
        anki=[
            {"front": "Что такое user story?", "back": "Краткое описание ценности для роли: As a… I want… so that…"},
            {"front": "Зачем acceptance criteria?", "back": "Определяют проверяемое «готово» для истории."},
            {"front": "Что значит Testable в INVEST?", "back": "Можно проверить, что история выполнена."},
            {"front": "Анти-паттерн требований", "back": "Формулировка без сценария и без критериев приёмки."},
        ],
        summary=[
            "История = роль + цель + ценность",
            "Критерии приёмки обязательны",
            "INVEST — чеклист качества",
        ],
    ),
    article(
        n=2,
        slug="map-product-backlog",
        title="Приоритизация бэклога",
        short="Бэклог",
        rubric="api",
        intro=(
            "Владелец продукта ранжирует работу: ценность, риск, зависимости. "
            "На собеседовании важно назвать хотя бы один метод и его ограничения."
        ),
        sections=[
            {
                "heading": "Методы",
                "body": (
                    "- MoSCoW: Must / Should / Could / Won't\n"
                    "- Value vs Effort: матрица быстрых побед\n"
                    "- RICE: Reach × Impact × Confidence / Effort"
                ),
            },
            {
                "heading": "Практика",
                "body": (
                    "Бэклог — упорядоченный список, не свалка идей. "
                    "Переупорядочивайте при новой информации; фиксируйте почему Must выше Should."
                ),
            },
        ],
        anki=[
            {"front": "Что такое MoSCoW?", "back": "Must / Should / Could / Won't — приоритеты объёма."},
            {"front": "Формула RICE", "back": "Reach × Impact × Confidence / Effort"},
            {"front": "Зачем упорядоченный бэклог?", "back": "Команда всегда знает, что брать следующим."},
            {"front": "Ограничение Value vs Effort", "back": "Субъективные оценки; нужна калибровка команды."},
        ],
        summary=["Бэклог упорядочен", "Метод приоритезации осознан", "Must не равен весь список"],
    ),
    article(
        n=3,
        slug="map-normalization",
        title="Нормализация и моделирование данных",
        short="Нормализация",
        rubric="data",
        intro=(
            "Нормализация уменьшает дублирование и аномалии обновления. "
            "На собеседовании достаточно 1–3 НФ и понимания когда денормализуют."
        ),
        sections=[
            {
                "heading": "1–3 НФ коротко",
                "body": (
                    "1НФ: атомарные значения, есть ключ.\n"
                    "2НФ: нет частичных зависимостей от составного ключа.\n"
                    "3НФ: нет транзитивных зависимостей неключевых атрибутов."
                ),
            },
            {
                "heading": "Денормализация",
                "body": (
                    "Читаемость и скорость отчётов иногда важнее строгой 3НФ. "
                    "Фиксируйте инварианты и кто обновляет дубли."
                ),
            },
        ],
        anki=[
            {"front": "Что требует 1НФ?", "back": "Атомарные значения и уникальный идентификатор строки."},
            {"front": "Что запрещает 2НФ?", "back": "Частичную зависимость атрибута от части составного ключа."},
            {"front": "Что запрещает 3НФ?", "back": "Транзитивные зависимости неключевых атрибутов."},
            {"front": "Зачем денормализуют?", "back": "Ускорить чтение/отчёты ценой контролируемого дублирования."},
        ],
        summary=["1–3 НФ знать наизусть", "Денормализация — осознанный trade-off"],
    ),
    article(
        n=4,
        slug="map-sql-nosql",
        title="SQL и NoSQL: когда что выбирать",
        short="SQL/NoSQL",
        rubric="data",
        intro=(
            "Реляционная БД сильна контрактом схемы и JOIN. "
            "Документные/ключ-значение удобны при гибкой схеме и горизонтальном росте."
        ),
        sections=[
            {
                "heading": "Сравнение",
                "body": (
                    "| | SQL | NoSQL |\n|---|---|---|\n"
                    "| Схема | Строгая | Гибкая |\n"
                    "| Транзакции | ACID (часто) | Зависит от СУБД |\n"
                    "| Масштаб | Вертикальный + шардинг | Горизонтальный из коробки |"
                ),
            },
            {
                "heading": "Выбор",
                "body": (
                    "Сложные связи и отчёты → SQL. "
                    "Кэш, сессии, события, профили с разной формой → Redis/Mongo и т.п."
                ),
            },
        ],
        anki=[
            {"front": "Сильная сторона SQL?", "back": "Схема, JOIN, предсказуемые транзакции."},
            {"front": "Когда NoSQL уместен?", "back": "Гибкая схема, горизонтальный масштаб, простые ключи доступа."},
            {"front": "Миф про NoSQL", "back": "«Всегда быстрее» — нет, зависит от доступа и нагрузки."},
            {"front": "Можно ли смешивать?", "back": "Да: Postgres + Redis — частый паттерн."},
        ],
        summary=["Выбор от доступа к данным", "Не религия стека"],
    ),
    article(
        n=5,
        slug="map-redis",
        title="Redis как кэш и структуры данных",
        short="Redis",
        rubric="data",
        intro=(
            "Redis — in-memory хранилище: строки, хеши, списки, множества, TTL. "
            "На собеседовании ждут паттерн cache-aside и понимание потери данных при рестарте."
        ),
        sections=[
            {
                "heading": "Типичные сценарии",
                "body": (
                    "- Кэш ответа API (ключ = hash запроса)\n"
                    "- Сессии и rate limit\n"
                    "- Очереди/pub-sub для лёгких сигналов"
                ),
            },
            {
                "heading": "Осторожно",
                "body": (
                    "Не храните единственный источник правды без persistence. "
                    "Инвалидация кэша сложнее записи."
                ),
            },
        ],
        anki=[
            {"front": "Что такое Redis?", "back": "In-memory key-value с богатыми структурами и TTL."},
            {"front": "Паттерн cache-aside", "back": "Читаем кэш; miss → БД → пишем кэш."},
            {"front": "Риск Redis как sole source?", "back": "Данные могут пропасть при сбое без persistence."},
            {"front": "Зачем TTL?", "back": "Автоматическая протухлость кэша и лимитов."},
        ],
        summary=["Кэш ≠ БД", "TTL и инвалидация обязательны в дизайне"],
    ),
    article(
        n=6,
        slug="map-cicd",
        title="CI/CD обзор",
        short="CI/CD",
        rubric="tools",
        intro=(
            "Continuous Integration — частые сборки и проверки на каждый push. "
            "Continuous Delivery/Deployment — автоматизированная доставка артефакта."
        ),
        sections=[
            {
                "heading": "Пайплайн",
                "body": (
                    "1. Checkout\n2. Install / build\n3. Lint + unit/integration tests\n"
                    "4. Сборка образа / артефакта\n5. Deploy в staging → prod (с одобрением или auto)"
                ),
            },
            {
                "heading": "Инструменты",
                "body": (
                    "GitHub Actions, GitLab CI, Jenkins — разный UX, одна идея: "
                    "воспроизводимый пайплайн как код (YAML/Jenkinsfile)."
                ),
            },
        ],
        anki=[
            {"front": "Что такое CI?", "back": "Автосборка и проверки на каждое изменение в репозитории."},
            {"front": "Отличие CD Delivery и Deploy", "back": "Delivery готов к выкладке; Deploy выкладывает автоматически."},
            {"front": "Зачем pipeline as code?", "back": "Версионируется, ревьюится, не живёт только в UI."},
            {"front": "Минимальный полезный CI", "back": "Install + тесты + линт на PR."},
        ],
        summary=["CI ловит регрессии рано", "Пайплайн в репозитории"],
    ),
    article(
        n=7,
        slug="map-k8s",
        title="Kubernetes обзор",
        short="Kubernetes",
        rubric="tools",
        intro=(
            "Kubernetes оркестрирует контейнеры: Pod, Deployment, Service, Ingress. "
            "После Docker/Compose это следующий уровень для нескольких реплик и самовосстановления."
        ),
        sections=[
            {
                "heading": "Базовые объекты",
                "body": (
                    "- Pod — минимальная единица запуска\n"
                    "- Deployment — желаемое число реплик и rolling update\n"
                    "- Service — стабильный сетевой доступ к подам\n"
                    "- Ingress — HTTP вход снаружи"
                ),
            },
            {
                "heading": "Когда рано",
                "body": (
                    "Один сервис на одном сервере часто закрывается Compose. "
                    "k8s окупается при многих сервисах, автоскейле и политике доставки."
                ),
            },
        ],
        anki=[
            {"front": "Что такое Pod?", "back": "Группа контейнеров с общей сетью/томами — единица планирования."},
            {"front": "Зачем Deployment?", "back": "Держит N реплик и обновляет без ручного ssh."},
            {"front": "Роль Service", "back": "Стабильный endpoint к набору подов."},
            {"front": "Когда k8s избыточен?", "back": "Простой стенд из 1–2 сервисов без нужды в оркестрации."},
        ],
        summary=["Pod / Deployment / Service", "Compose → k8s по необходимости"],
        diagrams=[
            {
                "caption": "Упрощённо",
                "mermaid": "flowchart LR\n  User --> Ingress\n  Ingress --> Svc[Service]\n  Svc --> Pod1\n  Svc --> Pod2",
            }
        ],
    ),
    article(
        n=8,
        slug="map-networking",
        title="Сети и путь HTTP-запроса",
        short="Сети/HTTP",
        rubric="tools",
        intro=(
            "Браузер → DNS → TCP → TLS → HTTP → сервер. "
            "На собеседовании полезно пройти путь запроса словами и назвать статус-коды."
        ),
        sections=[
            {
                "heading": "Слои на пальцах",
                "body": (
                    "DNS даёт IP. TCP устанавливает соединение. TLS шифрует. "
                    "HTTP несёт метод, путь, заголовки, тело."
                ),
            },
            {
                "heading": "Коды",
                "body": (
                    "2xx успех, 3xx редирект, 4xx ошибка клиента, 5xx ошибка сервера. "
                    "401 vs 403: не аутентифицирован vs нет прав."
                ),
            },
        ],
        anki=[
            {"front": "Порядок: DNS и TCP?", "back": "Сначала DNS (имя→IP), затем TCP handshake."},
            {"front": "Зачем TLS?", "back": "Шифрование и проверка сервера (HTTPS)."},
            {"front": "401 vs 403", "back": "401 — кто ты?; 403 — тебе нельзя."},
            {"front": "Что в HTTP-запросе?", "back": "Метод, URL/path, заголовки, опционально тело."},
        ],
        summary=["Путь запроса наизусть", "Смысл классов статус-кодов"],
    ),
    article(
        n=9,
        slug="map-auth-jwt",
        title="Аутентификация и JWT",
        short="Auth/JWT",
        rubric="tools",
        intro=(
            "Аутентификация — кто вы. Авторизация — что можно. "
            "JWT — самодостаточный токен с подписью; храните осторожно."
        ),
        sections=[
            {
                "heading": "Сессия vs JWT",
                "body": (
                    "Сессия на сервере: cookie session id, состояние в Redis/БД. "
                    "JWT: claims в токене, проверка подписи без round-trip (до отзыва)."
                ),
            },
            {
                "heading": "Практика",
                "body": (
                    "Короткий access + refresh, HTTPS only, не кладите секреты в payload. "
                    "Logout = blacklist/ротация refresh."
                ),
            },
        ],
        anki=[
            {"front": "AuthN vs AuthZ", "back": "Кто вы vs какие права."},
            {"front": "Что проверяет сервер в JWT?", "back": "Подпись, срок (exp), aud/iss при необходимости."},
            {"front": "Риск JWT в localStorage", "back": "XSS может украсть токен."},
            {"front": "Зачем refresh token?", "back": "Обновлять короткий access без повторного логина."},
        ],
        summary=["AuthN ≠ AuthZ", "Подпись и срок JWT", "Хранение токена — угроза XSS"],
    ),
    article(
        n=10,
        slug="map-https-access",
        title="HTTPS и разграничение доступа",
        short="HTTPS/доступ",
        rubric="tools",
        intro=(
            "HTTPS защищает канал. Разграничение доступа — кто к каким ресурсам допущен: "
            "ACL, RBAC, уровни секретности."
        ),
        sections=[
            {
                "heading": "HTTPS",
                "body": (
                    "Сертификат подтверждает сервер. Без TLS логин и cookie видны в сети. "
                    "HSTS снижает риск отката на HTTP."
                ),
            },
            {
                "heading": "Модели доступа",
                "body": (
                    "- ACL: списки на объект/пользователя\n"
                    "- RBAC: роли → права\n"
                    "- Матрица доступа: субъекты × объекты"
                ),
            },
        ],
        anki=[
            {"front": "Зачем HTTPS?", "back": "Шифрование трафика и проверка сервера."},
            {"front": "Что такое RBAC?", "back": "Права выдаются через роли, не поштучно каждому."},
            {"front": "ACL коротко", "back": "Список кто и с какими правами к ресурсу."},
            {"front": "Риск HTTP-логина", "back": "Перехват пароля/cookie в открытой сети."},
        ],
        summary=["HTTPS обязателен для логина", "RBAC проще масштабировать"],
    ),
    article(
        n=11,
        slug="map-qa",
        title="QA и тест-дизайн",
        short="QA",
        rubric="tools",
        intro=(
            "Тестирование снижает риск релиза. Пирамида: много быстрых unit, меньше integration, "
            "ещё меньше дорогих E2E. Тест-дизайн выбирает сценарии."
        ),
        sections=[
            {
                "heading": "Виды",
                "body": (
                    "- Функциональные / регресс\n"
                    "- API-тесты по контракту\n"
                    "- Негативные кейсы и границы"
                ),
            },
            {
                "heading": "Артефакты",
                "body": (
                    "Чек-лист, тест-кейс (шаги + ожидаемый результат), баг-репорт с воспроизведением."
                ),
            },
        ],
        anki=[
            {"front": "Пирамида тестирования", "back": "Unit > integration > E2E по количеству/скорости."},
            {"front": "Что в хорошем баг-репорте?", "back": "Шаги, ожидаемое, фактическое, окружение."},
            {"front": "Зачем негативные кейсы?", "back": "Проверяют отказоустойчивость и валидацию."},
            {"front": "Регресс", "back": "Повторная проверка, что старое не сломалось."},
        ],
        summary=["Пирамида", "Воспроизводимый баг-репорт"],
    ),
    article(
        n=12,
        slug="map-e2e",
        title="E2E сценарии локально",
        short="E2E",
        rubric="tools",
        intro=(
            "E2E гоняет браузер против живого UI. На 9to18 для этого есть локальный "
            "e2e-tester (Docker, Playwright) на 127.0.0.1:8300 — без облачной панели."
        ),
        sections=[
            {
                "heading": "Практика",
                "body": (
                    "1. Поднимите цель (UI) и tester контейнер\n"
                    "2. Задайте TARGET_UI_URL\n"
                    "3. Соберите сценарий (YAML/JSON) или через Discovery\n"
                    "4. Смотрите HTML/ZIP отчёт"
                ),
            },
            {
                "heading": "Стабильность",
                "body": (
                    "Ждите URL/текст, избегайте хрупких селекторов, отделяйте smoke от глубоких сюитов."
                ),
            },
        ],
        anki=[
            {"front": "Где панель e2e-tester?", "back": "Локально http://127.0.0.1:8300 после docker compose."},
            {"front": "Что такое Playwright E2E?", "back": "Автоматизация браузера: клики, заполнение, assert."},
            {"front": "Зачем TARGET_UI_URL?", "back": "Указывает Chromium, какой сайт тестировать."},
            {"front": "Артефакты прогона", "back": "Скриншоты, HTML-отчёт, ZIP."},
        ],
        summary=["Только локальный запуск", "Стабильные селекторы и ожидания"],
        lab=(
            "**30 минут.** Поднимите `deploy/e2e-tester` по README, откройте панель, "
            "запустите smoke-пример и сохраните отчёт."
        ),
    ),
    article(
        n=13,
        slug="map-soft-skills",
        title="Поведенческие вопросы на собеседовании",
        short="Soft skills",
        rubric="architecture",
        intro=(
            "STAR: Situation, Task, Action, Result. Готовьте 3–5 историй: конфликт, ошибка, "
            "лидерство без должности, обучение."
        ),
        sections=[
            {
                "heading": "Структура ответа",
                "body": (
                    "Короткий контекст → ваша роль → конкретные действия → измеримый итог. "
                    "Избегайте «мы всё сделали» без вашего вклада."
                ),
            },
            {
                "heading": "Темы",
                "body": (
                    "Дедлайн, разногласие в команде, фидбек, провал и вывод, менторство."
                ),
            },
        ],
        anki=[
            {"front": "Что такое STAR?", "back": "Situation, Task, Action, Result."},
            {"front": "Чего избегать в ответе?", "back": "Размытого «мы» без личных действий и итога."},
            {"front": "Сколько историй подготовить?", "back": "3–5 универсальных под разные вопросы."},
            {"front": "Зачем Result?", "back": "Показать эффект: метрика, урок, изменение процесса."},
        ],
        summary=["STAR", "Личный вклад и итог"],
    ),
]


def main() -> None:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in data if isinstance(item, dict)}
    added = 0
    for item in ARTICLES:
        if item["slug"] in by_slug:
            # replace to keep content fresh
            idx = next(i for i, row in enumerate(data) if row.get("slug") == item["slug"])
            data[idx] = item
        else:
            data.append(item)
            added += 1
        print(f"OK {item['slug']} anki={len(item['structured']['anki'])}")
    SEED.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Seed size={len(data)} added_new={added}")


if __name__ == "__main__":
    main()
