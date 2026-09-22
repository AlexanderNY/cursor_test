---
slug: jv-interview-drill
title: Interview drill Java/enterprise
shortTitle: JV drill
episode: JV15
rubric: tools
order: 815
publishedAt: 2027-06-29T10:00:00+03:00
profiles: [developer]
level: senior
tags: [java, drill, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Быстрые ответы JDBC/ORM/JMS/ESB.
prerequisites: [jv-adr-bus-vs-broker]
seoTitle: JV drill — senior
seoDescription: Быстрые ответы JDBC/ORM/JMS/ESB.
seoKeywords: [java, drill, собеседование]
canonicalUrl: https://9to18.ru/game/learn/jv-interview-drill
---

## Введение

Таймер 60–90 секунд на вопрос.

## Раздел: Основы

Пул вопросов: PreparedStatement, pool, N+1, queue vs topic, адаптер ESB, dual-write.

## Раздел: Практика

После ❌ — возврат к slug выпуска.

## Раздел: На собесе

Запишите свои формулировки, не чужие.

## Лаба

**Цель.** Пройти 10 вопросов вслух.

**Шаги.**
1. JDBC injection.
2. Зачем pool.
3. N+1 лечение.
4. DLQ.
5. ESB vs брокер.
6. Отметить ❌.
7. Повторить Anki.
8. Ссылка на capstone.

**В группу:** парный drill.

**Готово, если…**
- [ ] 10 ответов
- [ ] Gap-list
- [ ] Готовность к JV16

## Схема: Drill

```mermaid
flowchart LR
  Q --> A --> Review --> Fix
```

## Тест

### Формат drill?

**Ответ:** таймер + запись пробелов

**Пояснение:** Как SA23/SQL15.

### Главный JDBC must?

**Ответ:** PreparedStatement

**Пояснение:** Безопасность и ясность.

### Главный ORM trap?

**Ответ:** N+1

**Пояснение:** Логи SQL.

## Шпаргалка

<h3>Drill</h3><ul><li>60с</li><li>gap-list</li><li>повтор slug</li></ul>

## Anki

### Front: drill

Back: тренировка ответов

### Front: gap-list

Back: список ❌

### Front: N+1

Back: главный ORM trap

## Итоги

- Говорите вслух
- Чините пробелы
- Дальше capstone

## Ссылки

- Learn | [JV07](/game/learn/jv-jpa-nplus1)
- Далее: [Capstone](/game/learn/jv-capstone)
