"""Unit tests for Learn article Markdown import/export."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_HELPER_PATH = Path(__file__).resolve().parents[1] / "services" / "learn_article_md.py"
_SPEC = importlib.util.spec_from_file_location("learn_article_md", _HELPER_PATH)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)

parse_learn_article_md = _mod.parse_learn_article_md
serialize_learn_article_md = _mod.serialize_learn_article_md
load_article_template = _mod.load_article_template


SAMPLE_MD = """---
slug: jwt-auth
title: JWT на собеседовании
shortTitle: JWT
episode: MAP12
rubric: api
order: 42
publishedAt: 2026-09-20T10:00:00+03:00
profiles: [analyst, developer, unknown_role]
level: senior
tags: [auth, jwt]
durationMin: 25
excerpt: Как устроен JWT.
prerequisites: [map-auth-basics]
author: Иван Петров
authorUrl: https://t.me/example
coverUrl: https://cdn.example.com/cover.webp
seoTitle: JWT SEO
seoDescription: Описание SEO
seoKeywords: [jwt, auth]
canonicalUrl: https://9to18.ru/game/learn/jwt-auth
---

## Введение

Кратко опишите тему выпуска и зачем она нужна на собеседовании или в работе.

## Раздел: Access vs refresh

Текст теории про токены.

## Лаба

**Цель.** Проверить JWT.

## Схема: Поток токена

```mermaid
sequenceDiagram
  Client->>API: Bearer
```

## Тест

### Что лежит в payload JWT?

**Ответ:** claims

**Пояснение:** не секреты

### Вопрос 2?

**Ответ:** два

**Пояснение:** ок

### Вопрос 3?

**Ответ:** три

**Пояснение:** ок

## Шпаргалка

<h3>Суть</h3>
<ul><li>header.payload.signature</li></ul>

## Anki

### Front: Из чего состоит JWT?

Back: header, payload, signature

### Front: Вопрос 2?

Back: ответ 2

### Front: Вопрос 3?

Back: ответ 3

## Итоги

- Подписываем, не шифруем

## Ссылки

- [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
"""


def test_parse_learn_article_md_frontmatter_and_sections() -> None:
    payload, warnings = parse_learn_article_md(SAMPLE_MD)
    assert payload["slug"] == "jwt-auth"
    assert payload["title"] == "JWT на собеседовании"
    assert payload["rubricId"] == "api"
    assert payload["order"] == 42
    assert payload["profiles"] == ["analyst", "developer"]
    assert payload["level"] == "senior"
    assert payload["tags"] == ["auth", "jwt"]
    assert payload["durationMin"] == 25
    assert payload["excerpt"] == "Как устроен JWT."
    assert payload["prerequisites"] == ["map-auth-basics"]
    assert payload["author"] == "Иван Петров"
    assert payload["authorUrl"] == "https://t.me/example"
    assert payload["coverUrl"] == "https://cdn.example.com/cover.webp"
    assert payload["seoTitle"] == "JWT SEO"
    assert payload["seoDescription"] == "Описание SEO"
    assert payload["seoKeywords"] == ["jwt", "auth"]
    assert payload["canonicalUrl"] == "https://9to18.ru/game/learn/jwt-auth"
    structured = payload["structured"]
    assert structured["version"] == 1
    assert "собеседовании" in structured["intro"]
    assert structured["sections"][0]["heading"] == "Access vs refresh"
    assert "Цель" in structured["lab"]
    assert structured["diagrams"][0]["mermaid"].startswith("sequenceDiagram")
    assert len(structured["quiz"]) == 3
    assert structured["quiz"][0]["answer"] == "claims"
    assert "<h3>Суть</h3>" in structured["cheatsheetHtml"]
    assert len(structured["anki"]) == 3
    assert structured["anki"][0]["front"].startswith("Из чего")
    assert structured["summary"] == ["Подписываем, не шифруем"]
    assert payload["links"][0]["href"].startswith("https://datatracker")
    assert any("unknown_role" in warning or "профиль" in warning for warning in warnings)


def test_serialize_roundtrip_keeps_labels() -> None:
    payload, _ = parse_learn_article_md(SAMPLE_MD)
    rendered = serialize_learn_article_md(payload)
    again, _ = parse_learn_article_md(rendered)
    assert again["slug"] == payload["slug"]
    assert again["profiles"] == payload["profiles"]
    assert again["level"] == payload["level"]
    assert again["author"] == payload["author"]
    assert again["coverUrl"] == payload["coverUrl"]
    assert again["seoTitle"] == payload["seoTitle"]
    assert again["structured"]["quiz"][0]["answer"] == "claims"
    assert again["structured"]["anki"][0]["back"].startswith("header")


def test_invalid_level_warns() -> None:
    md = """---
slug: x
title: X
level: godlike
rubric: tools
---

## Введение

Достаточно длинное введение для шаблона статьи Learn здесь.
"""
    payload, warnings = parse_learn_article_md(md)
    assert payload["level"] == ""
    assert any("уровен" in warning.lower() for warning in warnings)


def test_on_knowledge_map_flag_adds_tag() -> None:
    md = """---
slug: map-item
title: Карта
rubric: tools
onKnowledgeMap: true
tags: [sql]
---

## Введение

Достаточно длинное введение для шаблона статьи Learn здесь.
"""
    payload, _ = parse_learn_article_md(md)
    assert "собеседование" in payload["tags"]
    assert "sql" in payload["tags"]
    rendered = serialize_learn_article_md(payload)
    assert "onKnowledgeMap: true" in rendered


def test_on_knowledge_map_false_removes_tag() -> None:
    md = """---
slug: map-item
title: Карта
rubric: tools
onKnowledgeMap: false
tags: [sql, собеседование]
---

## Введение

Достаточно длинное введение для шаблона статьи Learn здесь.
"""
    payload, _ = parse_learn_article_md(md)
    assert "собеседование" not in [t.lower() for t in payload["tags"]]
    assert payload["tags"] == ["sql"]


def test_load_article_template_nonempty() -> None:
    text = load_article_template()
    assert "slug:" in text
    assert "## Введение" in text
    assert "profiles:" in text
    assert "seoTitle:" in text
    assert "onKnowledgeMap:" in text
