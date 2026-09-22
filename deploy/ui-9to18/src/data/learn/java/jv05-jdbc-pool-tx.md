---
slug: jv-jdbc-pool-tx
title: Пул соединений и транзакции JDBC
shortTitle: JDBC pool tx
episode: JV05
rubric: data
order: 805
publishedAt: 2027-06-09T10:00:00+03:00
profiles: [developer]
level: junior
tags: [java, jdbc, transactions, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Connection pool и autocommit; связь с SQL ACID.
prerequisites: [jv-jdbc-basics]
seoTitle: JDBC pool tx — junior
seoDescription: Connection pool и autocommit; связь с SQL ACID.
seoKeywords: [java, jdbc, transactions, собеседование]
canonicalUrl: https://9to18.ru/game/learn/jv-jdbc-pool-tx
---

## Введение

Открывать Connection на каждый запрос без пула — дорого. Транзакции связывают несколько DML.

## Раздел: Основы

Пул (HikariCP и др.) держит готовые соединения. autocommit=true — каждый statement сам по себе; false — явный commit/rollback.

## Раздел: Практика

См. [sql-acid-transactions](/game/learn/sql-acid-transactions).

## Раздел: На собесе

На собесе: «пул ограничивает число соединений к БД и снижает latency connect».

## Лаба

**Цель.** Описать границы транзакции перевода денег.

**Шаги.**
1. Зачем пул?
2. autocommit false — когда?
3. ROLLBACK при ошибке.
4. Риск утечки соединений.
5. Ссылка SQL08.

**В группу:** разберите deadlock на двух обновлениях.

**Готово, если…**
- [ ] Пул понятен
- [ ] commit/rollback
- [ ] Связь с ACID

## Схема: Пул

```mermaid
flowchart LR
  App --> Pool
  Pool --> C1
  Pool --> C2
  Pool --> DB[(DB)]
```

## Тест

### Зачем pool?

**Ответ:** переиспользование соединений

**Пояснение:** Меньше handshake/нагрузки.

### autocommit false

**Ответ:** явные границы транзакции

**Пояснение:** Несколько DML атомарно.

### Утечка Connection

**Ответ:** не вернули в пул / не закрыли

**Пояснение:** Исчерпание пула.

## Шпаргалка

<h3>Tx</h3><pre><code>c.setAutoCommit(false);
// DML
c.commit();</code></pre>

## Anki

### Front: pool

Back: кэш соединений

### Front: rollback

Back: откат tx

### Front: SQL08

Back: ACID канон

## Итоги

- Пул = must-have
- Tx на уровне приложения
- Читайте SQL08

## Ссылки

- Learn | [SQL08 ACID](/game/learn/sql-acid-transactions)
- Далее: [ORM concepts](/game/learn/jv-orm-concepts)
