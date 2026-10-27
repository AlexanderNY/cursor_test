---
slug: rd-pubsub-vs-queue
title: Capstone Redis — drill и чеклист
shortTitle: Capstone Redis
episode: RD08
rubric: data
order: 708
publishedAt: 2027-05-15T10:00:00+03:00
profiles: [developer, analyst]
level: senior
tags: [redis, capstone, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Итоговый drill Redis vs PostgreSQL и чеклист RD01–RD07.
prerequisites: [rd-pubsub-vs-queue]
seoTitle: Redis capstone checklist — senior
seoDescription: Чеклист серии Redis и drill сравнения с PostgreSQL.
seoKeywords: [redis, capstone, чеклист, собеседование]
canonicalUrl: https://9to18.ru/game/learn/rd-pubsub-vs-queue
---

## Введение

Финальный выпуск: собрать ответы серии и проверить пробелы перед собесом.

## Раздел: Чеклист уровней

**Junior:** KV, типы, TTL/persistence, не source of truth.

**Middle:** cache-aside, stampede, pub/sub vs брокер.

**Senior:** eviction, Sentinel/Cluster обзор.

## Раздел: Redis vs PostgreSQL

PostgreSQL — схема, JOIN, транзакции, отчёты. Redis — низкая задержка, кэш, счётчики, сигналы. Гибрид нормален. См. [sql-ddl-dml-dcl](/game/learn/sql-ddl-dml-dcl).

## Раздел: Индекс slug

| Ep | slug |
|----|------|
| RD01 | rd-kv-model |
| RD02 | rd-kv-model |
| RD03 | rd-ttl-persistence |
| RD04 | rd-ttl-persistence |
| RD05 | rd-ttl-persistence |
| RD06 | rd-pubsub-vs-queue |
| RD07 | rd-pubsub-vs-queue |
| RD08 | rd-pubsub-vs-queue |

## Лаба

**Цель.** Пройти drill из 8 вопросов по одному на выпуск.

**Шаги.**
1. Закройте SERIES и ответьте на 8 вопросов вслух по таймеру 60с.
2. Отметьте ❌ и откройте соответствующий slug.
3. Повторите Anki слабых выпусков.
4. Сформулируйте гибрид PG+Redis для своего pet-проекта.
5. Добавьте ссылку на map-redis / PY20 в конспект.

**В группу:** парный drill: вопрос → ответ → правка.

**Готово, если…**
- [ ] Есть персональный gap-list
- [ ] Умеете сравнить Redis и PG
- [ ] Знаете индекс slug

## Схема: Трек RD

```mermaid
flowchart LR
  RD01 --> RD02 --> RD03 --> RD04 --> RD05 --> RD06 --> RD07 --> RD08
```

## Тест

### Когда Redis, когда PostgreSQL?

**Ответ:** кэш/lookup/сигналы vs схема/JOIN/OLTP-правда

**Пояснение:** Гибрид частый.

### Главный риск stampede?

**Ответ:**  thrashing БД на hot key miss

**Пояснение:** Лечится lock/singleflight.

### Sentinel решает какую задачу?

**Ответ:** failover репликации

**Пояснение:** Не шардирование.

## Шпаргалка

<h3>Чеклист</h3>
<ul>
<li>KV + типы + TTL</li>
<li>cache-aside + stampede</li>
<li>pub/sub ≠ Kafka</li>
<li>eviction + HA обзор</li>
</ul>

## Anki

### Front: Индекс RD01

Back: rd-kv-model

### Front: Индекс RD04

Back: rd-ttl-persistence

### Front: Гибрид

Back: PG пишет правду, Redis ускоряет

## Итоги

- Capstone = чеклист + drill
- Не зубрите команды — сценарии
- Связки с SQL/SA/PY обязательны

## Ссылки

- Learn | [SERIES](/game/learn)
- Learn | [SQL01](/game/learn/sql-ddl-dml-dcl)
- Learn | [PY20](/game/learn/py-perf-packaging-alt-runtimes)
- Learn | [SA10](/game/learn/sa-sync-async-queues)
