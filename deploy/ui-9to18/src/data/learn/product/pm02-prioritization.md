---
slug: pm-product-management
title: Приоритизация — RICE и WSJF
shortTitle: Prioritization
episode: PM02
rubric: product
order: 902
publishedAt: 2027-07-03T10:00:00+03:00
profiles: [product_owner]
level: junior
tags: [product, rice, wsjf, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Фреймворки приоритизации бэклога.
prerequisites: [pm-product-management]
seoTitle: Prioritization — junior
seoDescription: Фреймворки приоритизации бэклога.
seoKeywords: [product, rice, wsjf, собеседование]
canonicalUrl: https://9to18.ru/game/learn/pm-product-management
---

## Введение

Приоритет — явный trade-off, не «всем важно».

## Раздел: Основы

RICE: Reach, Impact, Confidence, Effort. WSJF: Cost of Delay / Job Size (SAFe).

## Раздел: Практика

См. также USM: [sa-requirements-basics](/game/learn/sa-requirements-basics); severity≠priority у QA: [qa-test-design](/game/learn/qa-test-design).

## Раздел: На собесе

На собесе покажите цифры и допущения Confidence.

## Лаба

**Цель.** Посчитать RICE для 3 фич.

**Шаги.**
1. Оцените Reach.
2. Impact 0.5–3.
3. Confidence %.
4. Effort person-months.
5. Сравните с WSJF идеей CoD.

**В группу:** поспорьте о Confidence.

**Готово, если…**
- [ ] Считаете RICE
- [ ] Знаете WSJF идею
- [ ] Ссылки SA/QA

## Схема: RICE

```mermaid
flowchart LR
  R[Reach] --> Score
  I[Impact] --> Score
  C[Confidence] --> Score
  E[Effort] --> Score
```

## Тест

### RICE формула?

**Ответ:** (R*I*C)/E

**Пояснение:** Effort в знаменателе.

### WSJF?

**Ответ:** Cost of Delay / размер

**Пояснение:** SAFe-приоритизация.

### QA priority vs product?

**Ответ:** срочность бага vs ценность фичи

**Пояснение:** Разные шкалы.

## Шпаргалка

<h3>RICE</h3><pre><code>(Reach * Impact * Confidence) / Effort</code></pre>

## Anki

### Front: RICE

Back: reach impact confidence / effort

### Front: WSJF

Back: CoD / size

### Front: USM

Back: SA02

## Итоги

- Цифры + допущения
- Не святой грааль
- Кросс SA/QA

## Ссылки

- Learn | [SA02](/game/learn/sa-requirements-basics)
- Learn | [QA04](/game/learn/qa-test-design)
- Далее: [CJM](/game/learn/pm-cjm)
