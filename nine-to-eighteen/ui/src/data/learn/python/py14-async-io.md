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

## Раздел: Частые вопросы с собеседования
**Вопрос.** Asyncio или threads для HTTP-клиента к 100 API?

**Ответ.** Asyncio в одном потоке держит много ожидающих I/O без стека на поток — меньше overhead, если драйверы truly async. Threads проще с блокирующими библиотеками; смешивать блокирующий код в loop без `to_thread` нельзя.

**Вопрос.** Обходит ли asyncio GIL?

**Ответ.** Нет: один поток, один интерпретатор, GIL как у обычного кода. Выигрыш — не параллельный CPU, а конкурентное ожидание I/O без тысяч потоков. CPU-bound — processes или `to_thread` с ограниченным пулом.

**Вопрос.** Что такое event loop одной фразой?

**Ответ.** Цикл, который планирует coroutine: на `await` снимает задачу с CPU и будит, когда I/O готов. `asyncio.run` создаёт loop, выполняет main coroutine и закрывает ресурсы.

**Вопрос.** Почему `time.sleep` в async-функции плох?

**Ответ.** Блокирует весь event loop — все coroutine стоят. В async-коде `await asyncio.sleep`; для реального блокирующего вызова — `asyncio.to_thread` или отдельный worker pool.

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

**Ответ:** возвращает coroutine; нужен await

**Пояснение:** вызов async def не выполняет тело сразу.

### Когда asyncio выгоден?

**Ответ:** много одновременных I/O-ожиданий

**Пояснение:** не ускоряет чистый CPU в одном процессе.

### time.sleep в coroutine?

**Ответ:** блокирует весь event loop

**Пояснение:** нужен await asyncio.sleep.

### asyncio.gather vs create_task?

**Ответ:** gather ждёт группу; create_task планирует фоново

**Пояснение:** gather — удобный fan-in результатов.

### async vs threading для HTTP-клиента?

**Ответ:** async при тысячах соединений; threads проще при малом числе

**Пояснение:** оба не обходят GIL для CPU; async экономит потоки на I/O wait.

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

### Front: await что делает?

Back: приостанавливает coroutine до готовности awaitable

### Front: asyncio.to_thread зачем?

Back: вынести blocking CPU/IO в thread pool без блокировки loop

### Front: Coroutine vs Task?

Back: Task — coroutine, запланированная на event loop

## Итоги

- Async — про конкурентность I/O, не про магический параллелизм CPU
- Ошибки блокировки loop — частый fail на собесе
- Далее: GIL и память (PY15)

## Ссылки

- [PEP 492 — async/await](https://peps.python.org/pep-0492/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [DEBAGanov — индекс вопросов серии](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- Далее: [GIL и GC](/game/learn/py-threading-gil-gc)
