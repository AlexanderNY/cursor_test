"""Tests for Learn article mnemonic MD parse/serialize."""
from __future__ import annotations

from services.learn_article_md import parse_learn_article_md, serialize_learn_article_md


SAMPLE = """---
slug: mem-test
title: Test
shortTitle: Test
episode: MEM99
rubric: tools
order: 1
publishedAt: 2026-09-20T12:00:00+03:00
profiles: [developer]
level: junior
tags: [test]
onKnowledgeMap: false
durationMin: 10
excerpt: Test excerpt for mnemonic parse.
prerequisites: []
---

## Введение

Достаточно длинное введение, чтобы пройти базовые проверки длины текста статьи.

## Раздел: Теория

Текст теории про мнемотехники.

## Лаба

**Цель.** Практика.

## Схема: Схема

```mermaid
flowchart LR
  A --> B
```

## Тест

### Вопрос 1?

**Ответ:** ответ1

**Пояснение:** пояснение1

### Вопрос 2?

**Ответ:** ответ2

**Пояснение:** пояснение2

### Вопрос 3?

**Ответ:** ответ3

**Пояснение:** пояснение3

## Шпаргалка

<h3>Суть</h3><ul><li>пункт</li></ul>

## Anki

### Front: Q1?

Back: A1

### Front: Q2?

Back: A2

### Front: Q3?

Back: A3

## Мнемоника

### acronym: ACID
**Задание:** Запомните свойства.
**Элементы:**
- Atomicity
- Consistency
- Isolation
- Durability
**Подсказка:** первые буквы.
**Ответ:** ACID

## Итоги

- Пункт один
"""


def test_parse_mnemonics_section() -> None:
    payload, warnings = parse_learn_article_md(SAMPLE)
    assert not any("Мнемоника" in w for w in warnings)
    structured = payload["structured"]
    mnemonics = structured.get("mnemonics") or []
    assert len(mnemonics) == 1
    item = mnemonics[0]
    assert item["technique"] == "acronym"
    assert item["title"] == "ACID"
    assert item["answer"] == "ACID"
    assert item["items"] == [
        "Atomicity",
        "Consistency",
        "Isolation",
        "Durability",
    ]


def test_roundtrip_keeps_mnemonics() -> None:
    payload, _ = parse_learn_article_md(SAMPLE)
    md = serialize_learn_article_md(payload)
    again, warnings = parse_learn_article_md(md)
    assert not any("Мнемоника" in w for w in warnings)
    assert again["structured"]["mnemonics"][0]["technique"] == "acronym"
    assert again["structured"]["mnemonics"][0]["answer"] == "ACID"
