---
slug: py-async-io
title: Sync vs async — asyncio на middle-собесе
shortTitle: Asyncio
episode: PY14
rubric: api
order: 314
publishedAt: 2026-10-27T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, asyncio, async, io, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Чем sync отличается от async и когда event loop окупается.
prerequisites: [py-typing-pep8-static]
seoTitle: Python asyncio — middle
seoDescription: Синхронный и асинхронный код, non-blocking I/O.
seoKeywords: [python, asyncio, async, await]
canonicalUrl: https://9to18.ru/game/learn/py-async-io
---

## Введение

В источнике вопросов async затронут коротко — на реальном middle/senior собесе это центр бэкенд-разговора. Разберём sync vs async, event loop и типичные ошибки (блокировка в coroutine).

## Раздел: Синхронный и асинхронный код

Синхронный код выполняется последовательно: пока `time.sleep` или сетевой вызов блокирует поток, он ничего полезного параллельно в этом потоке не делает.

Асинхронный стиль (`async def` / `await`) позволяет в одном потоке переключаться между задачами на ожидании I/O. Планирует это **event loop** (`asyncio`). `await` отдаёт управление loop, пока ждём будущий результат.

```python
import asyncio

async def fetch(url: str) -> str:
    await asyncio.sleep(0.1)  # placeholder I/O
    return url

async def main():
    return await asyncio.gather(fetch("a"), fetch("b"))

asyncio.run(main())
```

## Раздел: Non-blocking I/O и ловушки

Non-blocking I/O — операции, которые не держат поток на ожидании готовности данных: loop регистрирует сокет и будит coroutine позже. Это ускоряет **много одновременных I/O**, не CPU-задачи (там снова GIL/процессы — PY15).

Типичные ошибки:
- вызвать блокирующий `requests`/`time.sleep` внутри `async def`;
- забыть `await`;
- создать «fire-and-forget» Task без обработки исключений;
- смешивать потоки и loop без `to_thread` / очередей.

Для CPU-bound куска из async-кода — `asyncio.to_thread` или отдельный процесс.

## Лаба

**Цель.** Сравнить sync и async на «имитации» I/O.

**Шаги.**
1. Три `time.sleep(0.2)` подряд vs три `await asyncio.sleep(0.2)` через `gather` — замерьте wall time.
2. Намеренно поставьте `time.sleep` внутрь async и покажите деградацию.
3. Оберните блокирующую функцию через `asyncio.to_thread`.
4. Напишите короткое объяснение: когда async не нужен.

**В группу:** FastAPI/aiohttp — где в вашем стеке уже async?

**Готово, если…**
- [ ] Объясняете event loop
- [ ] Не блокируете loop sleep/sync HTTP
- [ ] Отличаете I/O-bound выигрыш от CPU

## Схема: Event loop

```mermaid
sequenceDiagram
  participant Loop as event_loop
  participant T1 as task1
  participant T2 as task2
  Loop->>T1: run_until_await
  T1-->>Loop: await_IO
  Loop->>T2: run_until_await
  T2-->>Loop: await_IO
  Loop->>T1: IO_ready_resume
```

## Тест

### Чем async def отличается от def?

**Ответ:** возвращает coroutine; нужна await/scheduler

**Пояснение:** вызов async def не выполняет тело сразу — создаёт coroutine object.

### Когда asyncio выгоден?

**Ответ:** много одновременных I/O-ожиданий

**Пояснение:** не ускоряет чистый CPU в одном процессе.

### Что будет, если в coroutine вызвать time.sleep?

**Ответ:** заблокируется весь event loop

**Пояснение:** sleep синхронный; другие task не получат CPU до конца sleep.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>async/await + event loop для concurrent I/O</li>
<li>не блокировать loop</li>
<li>CPU → to_thread / processes</li>
</ul>
<h3>Код</h3>
<pre><code>async def main():
    await asyncio.gather(c1(), c2())
asyncio.run(main())
</code></pre>

## Anki

### Front: asyncio.run зачем?

Back: создать loop, выполнить coroutine, закрыть loop

### Front: gather делает что?

Back: concurrently запускает awaitables и собирает результаты

### Front: Non-blocking I/O одной фразой?

Back: не держать поток в ожидании данных — продолжить другую работу

## Итоги

- Async — про конкурентность I/O, не про магический параллелизм CPU
- Ошибки блокировки loop — частый fail на собесе
- Далее: GIL и память (PY15)

## Ссылки

- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [DEBAGanov — sync/async](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- Далее: [GIL и GC](/game/learn/py-threading-gil-gc)
