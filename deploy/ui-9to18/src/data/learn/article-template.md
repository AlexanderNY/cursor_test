---
slug: jwt-auth
title: JWT на собеседовании
shortTitle: JWT
episode: MAP12
rubric: api
order: 42
publishedAt: 2026-09-20T10:00:00+03:00
profiles: [analyst, developer]
level: senior
tags: [auth, jwt, security, собеседование]
onKnowledgeMap: true
durationMin: 25
excerpt: Как устроен JWT и где его ломают на собеседовании.
prerequisites: [map-auth-basics]
author: Иван Петров
authorUrl: https://t.me/example
coverUrl: https://cdn.example.com/learn/jwt-cover.webp
seoTitle: JWT на собеседовании — трек аналитика, senior
seoDescription: Разбор JWT для собеседования: payload, refresh, типичные дыры. Трек аналитика, уровень senior.
seoKeywords: [jwt, auth, senior, аналитик]
canonicalUrl: https://9to18.ru/game/learn/jwt-auth
---

## Введение

Кратко опишите тему выпуска и зачем она нужна на собеседовании или в работе. Минимум ~40 символов.

## Раздел: Access vs refresh

Текст теории. Можно несколько разделов — каждый начинается с `## Раздел: …`.

## Лаба

**Цель.** …

**Шаги.**
1. …

**В группу:** …

**Готово, если…**
- [ ] …

## Схема: Поток токена

```mermaid
sequenceDiagram
  Client->>API: Authorization Bearer
  API-->>Client: 200 OK
```

## Тест

### Что лежит в payload JWT?

**Ответ:** claims

**Пояснение:** не секреты, а утверждения.

### Зачем нужен refresh-токен?

**Ответ:** обновить access без повторного логина

**Пояснение:** access живёт коротко, refresh — дольше и хранится осторожнее.

### Можно ли хранить JWT в localStorage?

**Ответ:** риск XSS

**Пояснение:** часто безопаснее httpOnly cookie при контроле CSRF.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>header.payload.signature</li>
<li>подписываем, не шифруем</li>
</ul>
<h3>Команды / формулы</h3>
<pre><code>Authorization: Bearer &lt;token&gt;</code></pre>

## Anki

### Front: Из чего состоит JWT?

Back: header, payload, signature

### Front: Чем access отличается от refresh?

Back: access короткий для API; refresh длиннее для обновления сессии

### Front: Что нельзя класть в payload?

Back: секреты и пароли — payload читается без ключа

## Итоги

- Подписываем, не шифруем
- Короткий access + осторожный refresh
- XSS и storage — частый вопрос на собесе

## Ссылки

- [RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
- Learn | /game/learn
