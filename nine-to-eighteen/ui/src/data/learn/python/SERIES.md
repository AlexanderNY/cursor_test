# Серия Python Learn: Junior → Senior

Карта 24 выпусков для трека разработчика. Пишите тела по [`../article-template.md`](../article-template.md).

**Все 24 выпуска** имеют полный текст (`py01-….md` … `py24-….md`) и залиты в `learn_seed.json` / `episodes.ts`.

Источник тем и номеров вопросов: [DEBAGanov — 400 вопросов Python](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md). В постах — **оригинальные** разборы, не копипаст ответов из источника.

## Конвенции

| Поле | Значение |
|------|----------|
| Файлы постов | `py01-….md` … `py24-….md` рядом с этим файлом |
| `episode` | `PY01` … `PY24` |
| `order` | `301` … `324` |
| `profiles` | `[developer]` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| `prerequisites` | предыдущий slug (линейный трек) |
| Seed | `core/data/learn_seed.json` → `generate_learn_episodes_ts.py` |

---

## Junior · `level: junior` · PY01–PY08

### PY01 · `py-intro-python`

```yaml
---
slug: py-intro-python
title: Python на собесе — язык, интерпретатор, когда уместен
shortTitle: Intro Python
episode: PY01
rubric: tools
order: 301
publishedAt: 2026-10-01T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, intro, собеседование]
onKnowledgeMap: true
durationMin: 25
excerpt: Чем Python является на практике, как исполняется код и когда его выбирать.
prerequisites: []
seoTitle: Python intro — junior, собеседование
seoDescription: Язык, интерпретатор, плюсы и минусы Python для junior-собеса.
seoKeywords: [python, junior, интерпретатор, собеседование]
canonicalUrl: https://9to18.ru/game/learn/py-intro-python
---
```

**Разделы (план):**
- Что такое Python и как устроен цикл исполнения (bytecode → CPython)
- Императивность / динамическая типизация / «всё объект»
- Когда брать Python и когда нет; Python 2 vs 3 (кратко)
- Типичные «лёгкий язык?» и недостатки на собесе

**Вопросы источника:** 1, 2, 51, 52, 74, 102, 103, 104, 105, 167, 266, 279, 289, 321, 347, 350, 351, 352, 353, 355, 360, 361, 377

**Тело:** [`py01-intro-python.md`](py01-intro-python.md)

---

### PY02 · `py-types-collections`

```yaml
---
slug: py-types-collections
title: Типы и коллекции — list, tuple, dict, set
shortTitle: Коллекции
episode: PY02
rubric: data
order: 302
publishedAt: 2026-10-03T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, collections, list, dict, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Встроенные типы и когда выбирать list, tuple, dict, set или frozenset.
prerequisites: [py-intro-python]
seoTitle: Python коллекции — junior
seoDescription: list/tuple/dict/set, срезы, ключи словаря — разбор для собеса.
seoKeywords: [python, list, dict, tuple, set]
canonicalUrl: https://9to18.ru/game/learn/py-types-collections
---
```

**Разделы (план):**
- Числа, bool, str и классы встроенных типов
- list vs tuple; отрицательные индексы и slice
- dict/set: что может быть ключом; frozenset; namedtuple
- append vs extend; когда какую структуру брать

**Вопросы источника:** 3, 8, 9, 20, 24, 25, 140, 141, 147, 150, 157, 171, 172, 191, 192, 193, 196, 223, 250, 251, 313, 314, 323, 324, 337, 356, 358, 369

**Тело:** [`py02-types-collections.md`](py02-types-collections.md)

---

### PY03 · `py-strings-ops-io`

```yaml
---
slug: py-strings-ops-io
title: Строки, операторы, ввод-вывод и файлы
shortTitle: Строки и I/O
episode: PY03
rubric: tools
order: 303
publishedAt: 2026-10-05T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, strings, files, io, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Операторы, строки, работа с файлами и базовый I/O на собеседовании.
prerequisites: [py-types-collections]
seoTitle: Python строки и файлы — junior
seoDescription: Операторы, строки, open/read, os — типовые вопросы junior.
seoKeywords: [python, str, files, operators]
canonicalUrl: https://9to18.ru/game/learn/py-strings-ops-io
---
```

**Разделы (план):**
- Арифметика, сравнение, логика, membership, identity, bitwise
- Строки: join/split, unicode, ord/chr, форматирование
- Файлы и пути: open, чтение/запись, os module
- Ввод данных, CLI-аргументы, случайные числа

**Вопросы источника:** 22, 111, 113, 148, 151, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 194, 195, 196, 197, 198, 199, 200, 205, 206, 207, 254, 264, 277, 308, 343, 359, 366, 380, 382

**Тело:** [`py01-intro-python.md`](py01-intro-python.md)

---

### PY04 · `py-control-flow-functions`

```yaml
---
slug: py-control-flow-functions
title: Управление потоком и функции — args, lambda, comprehensions
shortTitle: Функции
episode: PY04
rubric: tools
order: 304
publishedAt: 2026-10-07T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, functions, lambda, loops, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Циклы, функции, *args/**kwargs, lambda и list comprehensions.
prerequisites: [py-strings-ops-io]
seoTitle: Python функции и циклы — junior
seoDescription: for/while, функции, lambda, comprehensions для junior-собеса.
seoKeywords: [python, functions, lambda, comprehension]
canonicalUrl: https://9to18.ru/game/learn/py-control-flow-functions
---
```

**Разделы (план):**
- if/for/while, break/continue/else, pass, match/case (кратко)
- def, return, *args/**kwargs, дефолтные аргументы (mutable trap)
- lambda, map/filter/reduce на уровне junior; enumerate/zip
- List/dict comprehensions: когда писать и когда не писать

**Вопросы источника:** 4, 10, 13, 26, 115, 116, 117, 125, 126, 127, 128, 129, 178, 201, 202, 203, 204, 211, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 286, 287, 302, 303, 305, 317, 325, 357, 363, 364, 375, 387, 388, 398

**Тело:** [`py04-control-flow-functions.md`](py04-control-flow-functions.md)

---

### PY05 · `py-modules-packages-venv`

```yaml
---
slug: py-modules-packages-venv
title: Модули, пакеты, venv и менеджеры зависимостей
shortTitle: Модули и venv
episode: PY05
rubric: tools
order: 305
publishedAt: 2026-10-09T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, modules, venv, pip, собеседование]
onKnowledgeMap: true
durationMin: 25
excerpt: Как устроены модули и пакеты, зачем virtualenv и чем отличаются wheels.
prerequisites: [py-control-flow-functions]
seoTitle: Python модули и venv — junior
seoDescription: import, пакеты, venv, pip, wheels — база для junior.
seoKeywords: [python, venv, pip, modules]
canonicalUrl: https://9to18.ru/game/learn/py-modules-packages-venv
---
```

**Разделы (план):**
- module vs package; `__name__ == "__main__"`; reload
- sys.path, .pth, где лежат stdlib-модули
- venv / менеджеры пакетов; wheels vs eggs; зависимости
- Stdlib overview и упаковка своего кода (базово)

**Вопросы источника:** 21, 48, 69, 72, 73, 75, 81, 85, 98, 109, 130, 145, 146, 233, 234, 252, 253, 275, 309, 346, 349, 370, 392, 397

**Тело:** [`py05-modules-packages-venv.md`](py05-modules-packages-venv.md)

---

### PY06 · `py-oop-basics`

```yaml
---
slug: py-oop-basics
title: ООП в Python — class, self, наследование, property
shortTitle: ООП база
episode: PY06
rubric: architecture
order: 306
publishedAt: 2026-10-11T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, oop, class, inheritance, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Классы, экземпляры, наследование и property без магии метаклассов.
prerequisites: [py-modules-packages-venv]
seoTitle: Python ООП база — junior
seoDescription: self, __init__, inheritance, @property — junior OOP.
seoKeywords: [python, oop, class, property]
canonicalUrl: https://9to18.ru/game/learn/py-oop-basics
---
```

**Разделы (план):**
- class / instance / self / `__init__`; class vs instance attrs
- Наследование, super, isinstance; «интерфейсы» в Python
- @classmethod, @staticmethod, @property; accessors
- Полиморфизм и переопределение методов

**Вопросы источника:** 14, 18, 23, 27, 106, 107, 108, 136, 137, 138, 154, 155, 156, 224, 258, 259, 326, 327, 328, 329, 340, 345, 372, 373, 374, 399, 400

**Тело:** [`py06-oop-basics.md`](py06-oop-basics.md)

---

### PY07 · `py-exceptions`

```yaml
---
slug: py-exceptions
title: Исключения — try, иерархия и свои ошибки
shortTitle: Исключения
episode: PY07
rubric: tools
order: 307
publishedAt: 2026-10-13T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, exceptions, errors, собеседование]
onKnowledgeMap: true
durationMin: 25
excerpt: try/except/else/finally, иерархия Exception и кастомные ошибки.
prerequisites: [py-oop-basics]
seoTitle: Python исключения — junior
seoDescription: Обработка ошибок и иерархия исключений на собесе.
seoKeywords: [python, exceptions, try, finally]
canonicalUrl: https://9to18.ru/game/learn/py-exceptions
---
```

**Разделы (план):**
- try / except / else / finally / raise; NotImplementedError
- Иерархия исключений; деление на ноль и runtime errors
- Свои классы исключений; что если ошибку не поймали
- Паттерны «хорошей» обработки ошибок

**Вопросы источника:** 53, 93, 227, 228, 255, 256, 257, 328, 367, 368, 391, 393, 396

**Тело:** [`py07-exceptions.md`](py07-exceptions.md)

---

### PY08 · `py-stdlib-re-json-copy`

```yaml
---
slug: py-stdlib-re-json-copy
title: Stdlib на собесе — re, json, copy
shortTitle: re / json / copy
episode: PY08
rubric: tools
order: 308
publishedAt: 2026-10-15T10:00:00+03:00
profiles: [developer]
level: junior
tags: [python, re, json, copy, stdlib, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Регулярки, JSON, shallow/deep copy и соседние утилиты stdlib.
prerequisites: [py-exceptions]
seoTitle: Python re json copy — junior
seoDescription: re, json, copy — практический stdlib для junior.
seoKeywords: [python, regex, json, deepcopy]
canonicalUrl: https://9to18.ru/game/learn/py-stdlib-re-json-copy
---
```

**Разделы (план):**
- re: match/search, split/sub/subn; email-пример
- json dumps/loads; pickle vs json (сериализация)
- copy vs deepcopy; удаление файлов; shuffle списка
- Связка с файловым I/O из PY03

**Вопросы источника:** 38, 118, 119, 120, 133, 135, 142, 174, 197, 221, 225, 273, 311

**Тело:** [`py08-stdlib-re-json-copy.md`](py08-stdlib-re-json-copy.md)

---

## Middle · `level: middle` · PY09–PY16

### PY09 · `py-iterators-generators`

```yaml
---
slug: py-iterators-generators
title: Итераторы и генераторы — iter, next, yield
shortTitle: Итераторы
episode: PY09
rubric: api
order: 309
publishedAt: 2026-10-17T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, iterators, generators, yield, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Протокол итератора, генераторы и когда comprehensions лучше цикла.
prerequisites: [py-stdlib-re-json-copy]
seoTitle: Python итераторы и генераторы — middle
seoDescription: __iter__/__next__, yield, generator expressions на middle.
seoKeywords: [python, iterator, generator, yield]
canonicalUrl: https://9to18.ru/game/learn/py-iterators-generators
---
```

**Разделы (план):**
- Iterator protocol: `__iter__` / `__next__`
- Generators, yield; generator vs iterator
- Comprehensions и generator expressions
- Типичные ловушки (исчерпание, «перевернуть генератор»)

**Вопросы источника:** 32, 33, 34, 35, 87, 88, 268, 269, 270, 271, 272, 286, 287, 317, 331, 332, 333, 334, 335, 344, 364, 381, 387

**Тело:** [`py09-iterators-generators.md`](py09-iterators-generators.md)

---

### PY10 · `py-decorators-context`

```yaml
---
slug: py-decorators-context
title: Декораторы, замыкания и контекстные менеджеры
shortTitle: Декораторы
episode: PY10
rubric: api
order: 310
publishedAt: 2026-10-19T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, decorators, contextmanager, with, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Как пишут декораторы и with-менеджеры — частый блок middle-собеса.
prerequisites: [py-iterators-generators]
seoTitle: Python декораторы и with — middle
seoDescription: Декораторы, closures, context managers для middle.
seoKeywords: [python, decorator, with, closure]
canonicalUrl: https://9to18.ru/game/learn/py-decorators-context
---
```

**Разделы (план):**
- Замыкания и nonlocal
- Декораторы функций; retry-пример; зачем декораторы
- `with` и протоколы `__enter__` / `__exit__`
- contextlib; отличие от «просто try/finally»

**Вопросы источника:** 19, 36, 49, 131, 179, 209, 210, 371

**Тело:** [`py10-decorators-context.md`](py10-decorators-context.md)

---

### PY11 · `py-fp-collections-itertools`

```yaml
---
slug: py-fp-collections-itertools
title: FP в Python — map/filter/reduce, collections, itertools
shortTitle: FP и itertools
episode: PY11
rubric: data
order: 311
publishedAt: 2026-10-21T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, functional, collections, itertools, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Функциональный стиль и готовые структуры из collections/itertools.
prerequisites: [py-decorators-context]
seoTitle: Python FP collections itertools — middle
seoDescription: map/filter/reduce, Counter, itertools на middle-собесе.
seoKeywords: [python, map, filter, collections, itertools]
canonicalUrl: https://9to18.ru/game/learn/py-fp-collections-itertools
---
```

**Разделы (план):**
- map / filter / reduce / zip; higher-order functions
- Когда FP уместен рядом с ООП
- collections: Counter и соседи; itertools на практике
- Сравнение с comprehensions из PY09

**Вопросы источника:** 82, 134, 143, 158, 203, 215, 330, 338, 375, 388

**Тело:** [`py10-decorators-context.md`](py10-decorators-context.md)

---

### PY12 · `py-oop-advanced-mro`

```yaml
---
slug: py-oop-advanced-mro
title: ООП глубже — MRO, dunder, slots, namespaces
shortTitle: MRO и dunder
episode: PY12
rubric: architecture
order: 312
publishedAt: 2026-10-23T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, mro, dunder, slots, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: MRO, множественное наследование, магические методы и __slots__.
prerequisites: [py-fp-collections-itertools]
seoTitle: Python MRO и dunder — middle
seoDescription: MRO, __dict__, __slots__, namespaces для middle.
seoKeywords: [python, mro, dunder, slots]
canonicalUrl: https://9to18.ru/game/learn/py-oop-advanced-mro
---
```

**Разделы (план):**
- MRO и множественное наследование
- `__dict__`, globals/locals, LEGB / namespaces
- Dunder-методы; leading underscore convention
- `__slots__`; old-style vs new-style (история)

**Вопросы источника:** 15, 16, 41, 42, 54, 56, 95, 189, 229, 230, 231, 336, 348, 376, 385, 386

**Тело:** [`py12-oop-advanced-mro.md`](py12-oop-advanced-mro.md)

---

### PY13 · `py-typing-pep8-static`

```yaml
---
slug: py-typing-pep8-static
title: Стиль и качество — PEP 8, docstring, typing, linters
shortTitle: PEP 8 и typing
episode: PY13
rubric: tools
order: 313
publishedAt: 2026-10-25T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, pep8, typing, mypy, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Читаемый код, документация, аннотации типов и статический анализ.
prerequisites: [py-oop-advanced-mro]
seoTitle: Python PEP 8 typing — middle
seoDescription: PEP 8, docstring, type hints, flake8/mypy для middle.
seoKeywords: [python, pep8, typing, mypy]
canonicalUrl: https://9to18.ru/game/learn/py-typing-pep8-static
---
```

**Разделы (план):**
- PEP 8 и соглашения об именах
- docstring, `__doc__`, help/dir
- Type hints и mypy (дополнение сверх источника)
- Статический анализ: flake8/ruff/pylint; py_compile

**Вопросы источника:** 5, 6, 7, 12, 17, 58, 267

**Дополнение сверх источника:** typing / mypy — обязательно для middle.

**Тело:** [`py13-typing-pep8-static.md`](py13-typing-pep8-static.md)

---

### PY14 · `py-async-io`

```yaml
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
```

**Разделы (план):**
- Синхронный vs асинхронный код; пример async def
- Event loop и типичные ошибки (blocking в coroutine)
- Non-blocking I/O: смысл для I/O-bound сервисов
- Связь с GIL/threads (мост к PY15)

**Вопросы источника:** 28, 29, 395

**Дополнение сверх источника:** event loop, типичные ошибки — для собесов middle+.

**Тело:** [`py14-async-io.md`](py14-async-io.md)

---

### PY15 · `py-threading-gil-gc`

```yaml
---
slug: py-threading-gil-gc
title: Потоки, GIL, память и сборщик мусора
shortTitle: GIL и GC
episode: PY15
rubric: architecture
order: 315
publishedAt: 2026-10-29T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, gil, threading, gc, memory, собеседование]
onKnowledgeMap: true
durationMin: 40
excerpt: Threads vs processes, GIL, refcount/GC и отладка утечек памяти.
prerequisites: [py-async-io]
seoTitle: Python GIL GC память — middle
seoDescription: Многопоточность, GIL, управление памятью на middle/senior edge.
seoKeywords: [python, gil, gc, threading, memory]
canonicalUrl: https://9to18.ru/game/learn/py-threading-gil-gc
---
```

**Разделы (план):**
- Threading vs multiprocessing; жизненный цикл потоков
- GIL: зачем есть и что из этого следует
- Память: refcount, GC, id(), intern строк; dict/set internals
- Утечки и подход к отладке; передача аргументов (by object reference)

**Вопросы источника:** 11, 31, 39, 43, 55, 57, 60, 61, 64, 66, 92, 112, 121, 122, 123, 124, 126, 169, 261, 262, 301, 304, 310, 312, 322, 394

**Тело:** [`py15-threading-gil-gc.md`](py15-threading-gil-gc.md)

---

### PY16 · `py-testing-debug`

```yaml
---
slug: py-testing-debug
title: Тесты и отладка — unittest, pytest, pdb
shortTitle: Тесты и pdb
episode: PY16
rubric: tools
order: 316
publishedAt: 2026-10-31T10:00:00+03:00
profiles: [developer]
level: middle
tags: [python, testing, pytest, pdb, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Как тестировать и отлаживать Python-код на middle-уровне.
prerequisites: [py-threading-gil-gc]
seoTitle: Python testing pdb — middle
seoDescription: unittest/pytest-подход и pdb на собеседовании.
seoKeywords: [python, pytest, unittest, pdb]
canonicalUrl: https://9to18.ru/game/learn/py-testing-debug
---
```

**Разделы (план):**
- unittest: структура и подход к unit-тестам
- pytest: fixtures / parametrize (дополнение сверх источника)
- pdb и команды отладки
- Практический мини-цикл: падение → тест → фикс

**Вопросы источника:** 45, 212, 213, 214, 291, 292

**Дополнение сверх источника:** pytest fixtures/parametrize как практика проекта.

**Тело:** [`py15-threading-gil-gc.md`](py15-threading-gil-gc.md)

---

## Senior · `level: senior` · PY17–PY24

### PY17 · `py-descriptors-metaclasses`

```yaml
---
slug: py-descriptors-metaclasses
title: Дескрипторы и метаклассы
shortTitle: Метаклассы
episode: PY17
rubric: architecture
order: 317
publishedAt: 2026-11-02T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, descriptors, metaclasses, собеседование]
onKnowledgeMap: true
durationMin: 40
excerpt: Когда нужны дескрипторы и метаклассы — и когда это overkill.
prerequisites: [py-testing-debug]
seoTitle: Python дескрипторы и метаклассы — senior
seoDescription: descriptors, metaclasses, type() без class на senior-собесе.
seoKeywords: [python, descriptor, metaclass]
canonicalUrl: https://9to18.ru/game/learn/py-descriptors-metaclasses
---
```

**Разделы (план):**
- Дескрипторы vs декораторы; data/non-data descriptors
- Метаклассы: type, когда применять
- Создание класса без `class`
- Связь с `@property` и ORM-паттернами

**Вопросы источника:** 44, 47, 63, 341, 383, 384

**Тело:** [`py17-descriptors-metaclasses.md`](py17-descriptors-metaclasses.md)

---

### PY18 · `py-perf-packaging-alt-runtimes`

```yaml
---
slug: py-perf-packaging-alt-runtimes
title: Производительность, упаковка и альтернативные рантаймы
shortTitle: Perf и PyPy
episode: PY18
rubric: tools
order: 318
publishedAt: 2026-11-04T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, performance, pypy, cython, packaging, собеседование]
onKnowledgeMap: true
durationMin: 40
excerpt: Как ускорять Python, упаковывать код и когда смотреть на PyPy/Cython.
prerequisites: [py-descriptors-metaclasses]
seoTitle: Python perf packaging runtimes — senior
seoDescription: Ускорение, wheels, C-API, Cython/PyPy для senior.
seoKeywords: [python, pypy, cython, wheels, performance]
canonicalUrl: https://9to18.ru/game/learn/py-perf-packaging-alt-runtimes
---
```

**Разделы (план):**
- Профилирование и приёмы ускорения; NumPy vs list
- wheels, binary deps, PYTHONOPTIMIZE, `__pycache__`
- Cython / PyPy / IronPython; ctypes и C↔Python
- Упаковка и дистрибуция кода

**Вопросы источника:** 62, 67, 68, 70, 71, 76, 83, 86, 91, 110, 290, 339, 346

**Тело:** [`py17-descriptors-metaclasses.md`](py17-descriptors-metaclasses.md)

---

### PY19 · `py-web-flask-django`

```yaml
---
slug: py-web-flask-django
title: Веб-фреймворки — Flask, Django, Pyramid
shortTitle: Flask / Django
episode: PY19
rubric: api
order: 319
publishedAt: 2026-11-06T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, flask, django, web, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Сравнение веб-фреймворков и middleware в духе вопросов источника.
prerequisites: [py-perf-packaging-alt-runtimes]
seoTitle: Python Flask Django — senior
seoDescription: Flask vs Django/Pyramid, sessions, middleware.
seoKeywords: [python, flask, django, middleware]
canonicalUrl: https://9to18.ru/game/learn/py-web-flask-django
---
```

**Разделы (план):**
- Framework vs library; обзор Flask / Django / Pyramid
- Flask: WTF, sessions, MVC-взгляд, DB connection
- Middleware / context processors (Django-угол)
- Ссылка на FastAPI/CopyParse как современный сосед (без ухода от Q источника)

**Вопросы источника:** 90, 280, 294, 295, 296, 297, 298, 299, 354, 362, 378

**Тело:** [`py19-web-flask-django.md`](py19-web-flask-django.md)

---

### PY20 · `py-db-cache-memcached`

```yaml
---
slug: py-db-cache-memcached
title: БД и кеш — SQL из Python и Memcached pitfalls
shortTitle: БД и Memcached
episode: PY20
rubric: data
order: 320
publishedAt: 2026-11-08T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, sql, memcached, cache, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Доступ к БД из Python и типовые ловушки распределённого кеша.
prerequisites: [py-web-flask-django]
seoTitle: Python DB Memcached — senior
seoDescription: MySQL/SQL из Python и Memcached dogpile/failover.
seoKeywords: [python, sql, memcached, cache]
canonicalUrl: https://9to18.ru/game/learn/py-db-cache-memcached
---
```

**Разделы (план):**
- Выборка из БД (MySQL/SQL) через Python
- DML из скриптов; границы ORM vs raw SQL
- Memcached: downtime, dogpile, когда не использовать
- Failover и поведение при падении ноды

**Вопросы источника:** 164, 260, 281, 282, 283, 284, 285

**Тело:** [`py20-db-cache-memcached.md`](py20-db-cache-memcached.md)

---

### PY21 · `py-concurrency-io-patterns`

```yaml
---
slug: py-concurrency-io-patterns
title: Concurrency и I/O в проде — утечки, сигналы, диагностика
shortTitle: Prod concurrency
episode: PY21
rubric: architecture
order: 321
publishedAt: 2026-11-10T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, concurrency, production, debugging, собеседование]
onKnowledgeMap: true
durationMin: 35
excerpt: Неблокирующий I/O, утечки, сигналы и диагностика на Linux.
prerequisites: [py-db-cache-memcached]
seoTitle: Python prod concurrency — senior
seoDescription: Memory leaks, signals, remote files, non-blocking I/O.
seoKeywords: [python, concurrency, memory-leak, linux]
canonicalUrl: https://9to18.ru/game/learn/py-concurrency-io-patterns
---
```

**Разделы (план):**
- Non-blocking I/O в продакшен-контексте (углубление PY14)
- Утечки памяти: с чего начать отладку
- Сигналы; доступ к файлам/процессам на Linux (PID, ресурсы)
- Чеклист «упало в проде» для Python-сервиса

**Вопросы источника:** 92, 235, 301, 316, 319, 395

**Тело:** [`py21-concurrency-io-patterns.md`](py21-concurrency-io-patterns.md)

---

### PY22 · `py-design-dry-architecture`

```yaml
---
slug: py-design-dry-architecture
title: Дизайн — DRY, границы языка, когда не брать Python
shortTitle: DRY и границы
episode: PY22
rubric: architecture
order: 322
publishedAt: 2026-11-12T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, dry, architecture, design, собеседование]
onKnowledgeMap: true
durationMin: 25
excerpt: Архитектурные ответы senior: DRY через OOP/FP и выбор стека.
prerequisites: [py-concurrency-io-patterns]
seoTitle: Python DRY architecture — senior
seoDescription: DRY, когда использовать и не использовать Python.
seoKeywords: [python, dry, architecture]
canonicalUrl: https://9to18.ru/game/learn/py-design-dry-architecture
---
```

**Разделы (план):**
- DRY через OOP и FP
- Когда Python — правильный выбор
- Когда Python не брать
- Связка с перф/GIL/async из предыдущих выпусков

**Вопросы источника:** 351, 352, 353

**Тело:** [`py22-design-dry-architecture.md`](py22-design-dry-architecture.md)

---

### PY23 · `py-interview-tricky`

```yaml
---
slug: py-interview-tricky
title: Трюки собеса — «что выведет код»
shortTitle: Tricky drill
episode: PY23
rubric: tools
order: 323
publishedAt: 2026-11-14T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, interview, tricky, quiz, собеседование]
onKnowledgeMap: true
durationMin: 40
excerpt: Сжатый drill по выражениям, замыканиям и неочевидным результатам.
prerequisites: [py-design-dry-architecture]
seoTitle: Python interview tricky — senior
seoDescription: Разбор «что выведет» и классических ловушек Python.
seoKeywords: [python, interview, quiz, mutable-default]
canonicalUrl: https://9to18.ru/game/learn/py-interview-tricky
---
```

**Разделы (план):**
- Выражения и порядок операций; for/else сюрпризы
- Замыкания в цикле; mutable default (повтор с углублением)
- is vs ==, intern, неочевидный output
- Мини-набор задач «написать / исправить»

**Вопросы источника:** 30, 46, 50, 59, 65, 78, 84, 89, 94, 96, 99, 159, 160, 161, 208, 241, 263, 288, 327

**Тело:** [`py23-interview-tricky.md`](py23-interview-tricky.md)

---

### PY24 · `py-senior-capstone`

```yaml
---
slug: py-senior-capstone
title: Карта собеса Python — чеклист Junior→Senior
shortTitle: Capstone
episode: PY24
rubric: architecture
order: 324
publishedAt: 2026-11-16T10:00:00+03:00
profiles: [developer]
level: senior
tags: [python, checklist, interview, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Сводка трека: что закрыто серией и где искать пробелы.
prerequisites: [py-interview-tricky]
seoTitle: Python interview checklist — senior capstone
seoDescription: Чеклист Junior→Senior и ссылка на полный список вопросов.
seoKeywords: [python, interview, checklist, senior]
canonicalUrl: https://9to18.ru/game/learn/py-senior-capstone
---
```

**Разделы (план):**
- Чеклист по уровням: junior / middle / senior
- Как пользоваться серией перед собесом (Anki + тест)
- Пробелы и appendix-темы вне основной цепочки
- Ссылка на полный список вопросов 1–407

**Вопросы источника:** обзор покрытия серии; полный список 1–407 как внешняя шпаргалка

**Тело:** [`py24-senior-capstone.md`](py24-senior-capstone.md)

---

## Индекс покрытия: номер вопроса → slug

Первичное назначение темы. Дубликаты источника, попавшие в несколько выпусков по смыслу, указаны один раз (канонический пост). Номера без строки — см. appendix.

| Q | slug |
|---|------|
| 1–2 | py-intro-python |
| 3 | py-types-collections |
| 4 | py-control-flow-functions |
| 5–7 | py-typing-pep8-static |
| 8–9 | py-types-collections |
| 10 | py-control-flow-functions |
| 11 | py-threading-gil-gc |
| 12 | py-typing-pep8-static |
| 13 | py-control-flow-functions |
| 14 | py-oop-basics |
| 15–16 | py-oop-advanced-mro |
| 17 | py-typing-pep8-static |
| 18 | py-oop-basics |
| 19 | py-decorators-context |
| 20 | py-types-collections |
| 21 | py-modules-packages-venv |
| 22 | py-strings-ops-io |
| 23 | py-oop-basics |
| 24–25 | py-types-collections |
| 26 | py-control-flow-functions |
| 27 | py-oop-basics |
| 28–29 | py-async-io |
| 30 | py-interview-tricky |
| 31 | py-threading-gil-gc |
| 32–35 | py-iterators-generators |
| 36 | py-decorators-context |
| 38 | py-stdlib-re-json-copy |
| 39 | py-threading-gil-gc |
| 41–42 | py-oop-advanced-mro |
| 43 | py-threading-gil-gc |
| 44 | py-descriptors-metaclasses |
| 45 | py-testing-debug |
| 46 | py-interview-tricky |
| 47 | py-descriptors-metaclasses |
| 48 | py-modules-packages-venv |
| 49 | py-decorators-context |
| 50 | py-interview-tricky |
| 51–52 | py-intro-python |
| 53 | py-exceptions |
| 54 | py-oop-advanced-mro |
| 55 | py-threading-gil-gc |
| 56 | py-oop-advanced-mro |
| 57 | py-threading-gil-gc |
| 58 | py-typing-pep8-static |
| 59 | py-interview-tricky |
| 60–61 | py-threading-gil-gc |
| 62 | py-perf-packaging-alt-runtimes |
| 63 | py-descriptors-metaclasses |
| 64 | py-threading-gil-gc |
| 65 | py-interview-tricky |
| 66 | py-threading-gil-gc |
| 67–71 | py-perf-packaging-alt-runtimes |
| 72–73 | py-modules-packages-venv |
| 74 | py-intro-python |
| 75 | py-modules-packages-venv |
| 76 | py-perf-packaging-alt-runtimes |
| 78 | py-interview-tricky |
| 81–83 | py-modules-packages-venv (81); py-perf-packaging-alt-runtimes (83) |
| 82 | py-fp-collections-itertools |
| 84 | py-interview-tricky |
| 85 | py-modules-packages-venv |
| 86 | py-perf-packaging-alt-runtimes |
| 87–88 | py-iterators-generators |
| 89 | py-interview-tricky |
| 90 | py-web-flask-django |
| 91 | py-perf-packaging-alt-runtimes |
| 92 | py-threading-gil-gc / py-concurrency-io-patterns |
| 93 | py-exceptions |
| 94–96 | py-interview-tricky |
| 95 | py-oop-advanced-mro |
| 98 | py-modules-packages-venv |
| 99 | py-interview-tricky |
| 102–105 | py-intro-python |
| 106–108 | py-oop-basics |
| 109 | py-modules-packages-venv |
| 110 | py-perf-packaging-alt-runtimes |
| 111 | py-strings-ops-io |
| 112 | py-threading-gil-gc |
| 113 | py-strings-ops-io |
| 115–117 | py-control-flow-functions |
| 118–120 | py-stdlib-re-json-copy |
| 121–124 | py-threading-gil-gc |
| 125–129 | py-control-flow-functions |
| 130 | py-modules-packages-venv |
| 131 | py-decorators-context |
| 133 | py-stdlib-re-json-copy |
| 134 | py-fp-collections-itertools |
| 135 | py-stdlib-re-json-copy |
| 136–138 | py-oop-basics |
| 140–141 | py-types-collections |
| 142 | py-stdlib-re-json-copy |
| 143 | py-fp-collections-itertools |
| 145–146 | py-modules-packages-venv |
| 147 | py-types-collections |
| 148 | py-strings-ops-io |
| 150 | py-types-collections |
| 151 | py-strings-ops-io |
| 154–156 | py-oop-basics |
| 157 | py-types-collections |
| 158 | py-fp-collections-itertools |
| 159–161 | py-interview-tricky |
| 164 | py-db-cache-memcached |
| 167 | py-intro-python |
| 169 | py-threading-gil-gc |
| 171–172 | py-types-collections |
| 174 | py-stdlib-re-json-copy |
| 175–188 | py-strings-ops-io |
| 189 | py-oop-advanced-mro |
| 191–193 | py-types-collections |
| 194–200 | py-strings-ops-io |
| 201–204 | py-control-flow-functions |
| 205–207 | py-strings-ops-io |
| 208 | py-interview-tricky |
| 209–210 | py-decorators-context |
| 211 | py-control-flow-functions |
| 212–214 | py-testing-debug |
| 215 | py-fp-collections-itertools |
| 221 | py-stdlib-re-json-copy |
| 223–224 | py-types-collections (223); py-oop-basics (224) |
| 225 | py-stdlib-re-json-copy |
| 227–228 | py-exceptions |
| 229–231 | py-oop-advanced-mro |
| 233–234 | py-modules-packages-venv |
| 235 | py-concurrency-io-patterns |
| 238–249 | py-control-flow-functions |
| 250–251 | py-types-collections |
| 252–253 | py-modules-packages-venv |
| 254 | py-strings-ops-io |
| 255–257 | py-exceptions |
| 258–259 | py-oop-basics |
| 260 | py-db-cache-memcached |
| 261–262 | py-threading-gil-gc |
| 263 | py-interview-tricky |
| 264 | py-strings-ops-io |
| 266 | py-intro-python |
| 267 | py-typing-pep8-static |
| 268–272 | py-iterators-generators |
| 273 | py-stdlib-re-json-copy |
| 275 | py-modules-packages-venv |
| 277 | py-strings-ops-io |
| 279 | py-intro-python |
| 280 | py-web-flask-django |
| 281–285 | py-db-cache-memcached |
| 286–287 | py-control-flow-functions / py-iterators-generators |
| 288 | py-interview-tricky |
| 289 | py-intro-python |
| 290 | py-perf-packaging-alt-runtimes |
| 291–292 | py-testing-debug |
| 294–299 | py-web-flask-django |
| 301 | py-threading-gil-gc / py-concurrency-io-patterns |
| 302–303 | py-control-flow-functions |
| 304 | py-threading-gil-gc |
| 305 | py-control-flow-functions |
| 308 | py-strings-ops-io |
| 309 | py-modules-packages-venv |
| 310 | py-threading-gil-gc |
| 311 | py-stdlib-re-json-copy |
| 312 | py-threading-gil-gc |
| 313–314 | py-types-collections |
| 316 | py-concurrency-io-patterns |
| 317 | py-control-flow-functions / py-iterators-generators |
| 319 | py-concurrency-io-patterns |
| 321 | py-intro-python |
| 322 | py-threading-gil-gc |
| 323–325 | py-types-collections (323–324); py-control-flow-functions (325) |
| 326–329 | py-oop-basics |
| 330 | py-fp-collections-itertools |
| 331–335 | py-iterators-generators |
| 336 | py-oop-advanced-mro |
| 337 | py-types-collections |
| 338 | py-fp-collections-itertools |
| 339 | py-perf-packaging-alt-runtimes |
| 340 | py-oop-basics |
| 341 | py-descriptors-metaclasses |
| 343 | py-strings-ops-io |
| 344 | py-iterators-generators |
| 345 | py-oop-basics |
| 346 | py-modules-packages-venv / py-perf-packaging-alt-runtimes |
| 347 | py-intro-python |
| 348 | py-oop-advanced-mro |
| 349 | py-modules-packages-venv |
| 350–353 | py-intro-python / py-design-dry-architecture (351–353) |
| 354 | py-web-flask-django |
| 355 | py-intro-python |
| 356 | py-types-collections |
| 357 | py-control-flow-functions |
| 358 | py-types-collections |
| 359 | py-strings-ops-io |
| 360–361 | py-intro-python |
| 362 | py-web-flask-django |
| 363–364 | py-control-flow-functions / py-iterators-generators |
| 366 | py-strings-ops-io |
| 367–368 | py-exceptions |
| 369 | py-types-collections |
| 370 | py-modules-packages-venv |
| 371 | py-decorators-context |
| 372–374 | py-oop-basics |
| 375 | py-control-flow-functions / py-fp-collections-itertools |
| 376 | py-oop-advanced-mro |
| 377 | py-intro-python |
| 378 | py-web-flask-django |
| 380 | py-strings-ops-io |
| 381 | py-iterators-generators |
| 382 | py-strings-ops-io |
| 383–384 | py-descriptors-metaclasses |
| 385–386 | py-oop-advanced-mro |
| 387–388 | py-control-flow-functions / py-fp-collections-itertools |
| 391 | py-exceptions |
| 392 | py-modules-packages-venv (`__main__`) |
| 393 | py-exceptions |
| 394 | py-threading-gil-gc |
| 395 | py-async-io / py-concurrency-io-patterns |
| 396 | py-exceptions |
| 397 | py-modules-packages-venv |
| 398 | py-control-flow-functions |
| 399–400 | py-oop-basics |
| 401+ | py-senior-capstone (обзор; детали по теме return/instance — PY04/PY06) |

### Дубликаты источника (схлопнуты)

Повторы одной темы в разных номерах (list/tuple, generators, GIL, lambda, property, memory и т.д.) покрываются **одним** каноническим постом выше. В тесте/Anki конкретного выпуска можно ссылаться на несколько номеров одной темы.

### Appendix — вне основной цепочки

Узкие или устаревшие темы источника **не** входят в PY01–PY24 как отдельные выпуски. При желании — отдельные one-off посты позже:

| Q | Тема | Почему вне трека |
|---|------|------------------|
| 37 | Исполняемый скрипт cross-OS | Кратко закрыто в PY05/PY03 |
| 40 | globals — «хорошая идея?» | Частично PY12; отдельный пост не нужен |
| 77 | «Статическая» переменная в функции | Можно в PY10 (closures) |
| 79–80 | Словарь с нуля / one-liner caps | Алго-упражнения → PY23 при необходимости |
| 97, 132 | Monkey patching | Опционально к PY16/PY17 |
| 100–101 | Python 3.10 / медленный старт Windows | Устаревает; footnote в PY01 |
| 114 | range() | PY04 |
| 139, 144, 149, 152, 216–217 | Сортировки / NumPy-SciPy | Data-science ветка |
| 153 | TkInter | Desktop GUI вне трека |
| 162–163, 165–166, 173 | Мини-задачи на код | Лабы PY02–PY04 |
| 168 | Тернарный оператор | PY04 |
| 170 | help/dir | PY13 |
| 190 | Multiple assignment | PY03 |
| 218–220 | nonlocal / global / shebang | PY10 / PY05 |
| 222 | accessors/@property | PY06 |
| 226 | Как запустить скрипт | PY01/PY05 |
| 232 | Тройные кавычки | PY03/PY13 |
| 236 | Отправка почты | Инфра one-off |
| 237 | «Реализация» | Слишком размыто |
| 265 | «Приложения Python» | Обзор → PY01/PY19 |
| 274, 276, 278 | str/int, LEGB, // | Уже в PY03/PY12 |
| 293 | (пропуск нумерации в источнике) | — |
| 300, 306–307 | Сортировка/reverse/merge lists | Алго → лаба PY02/PY23 |
| 315 | Python vs Scala на Spark | Big data вне трека |
| 318 | Запуск Java-кода | Interop вне трека |
| 320 | Инструменты приёма данных | Data eng вне трека |
| 365 | «Массив» в Python | PY02 + NumPy appendix |
| 379 | exec/eval | Опционально PY23 (security note) |
| 389–390 | (пропуски/дубли в источнике) | — |

---

## Обслуживание

```bash
python core/scripts/import_python_learn_pilots.py
python core/scripts/generate_learn_episodes_ts.py
```

Скрипт подхватывает все `py*.md` в этой папке.
