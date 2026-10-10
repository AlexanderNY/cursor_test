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

## Введение

После базового ООП middle спрашивают MRO, dunder-методы, `__slots__` и пространства имён. Нужна точная картина lookup и когда multiple inheritance оправдан.

## Раздел: MRO и namespaces

При множественном наследовании Python строит **MRO** (Method Resolution Order, C3 linearization): `Class.__mro__` / `Class.mro()`. `super()` идёт по MRO, не «только родитель в скобках».

Пространства имён: builtins → module global → enclosing (nonlocal) → local (LEGB при чтении имён). `globals()`/`locals()` показывают словари контекста. Атрибуты экземпляра обычно в `__dict__`.

Соглашения: `_single` — internal; `__double` без хвоста — name mangling в классе; `__dunder__` — протоколы языка.

## Раздел: Dunder и slots

Магические методы задают поведение: `__str__`/`__repr__`, `__eq__`, `__len__`, арифметика, контекст, итерация. Не вызывайте их руками без нужды — используйте `str(x)`, `len(x)`.

`__slots__` фиксирует набор атрибутов, убирает per-instance `__dict__` (экономия памяти, запрет случайных полей). Ограничения: наследование slots нужно проектировать аккуратно.

Old-style classes — история Python 2; в Python 3 все classes new-style (наследники object).

## Раздел: Частые вопросы с собеседования
**Вопрос.** Зачем diamond inheritance и как Python его разрешает?

**Ответ.** Ромб: общий предок через две ветки. C3 linearization строит MRO без конфликтов: каждый класс появляется один раз, порядок сохраняет локальный порядок баз. `D.__mro__` показывает цепочку для `super()`.

**Вопрос.** Куда смотрит `super()` в множественном наследовании?

**Ответ.** На следующий класс в MRO текущего типа, не обязательно на «родителя в скобках». Кооперативные миксины строят цепочку вызовов через `super()`, а не прямой `Parent.method(self)`.

**Вопрос.** Зачем `__slots__`?

**Ответ.** Ограничивает набор атрибутов экземпляра, убирает per-instance `__dict__` — экономия памяти на миллионах однотипных объектов. Минус: нельзя добавить произвольный атрибут, наследование требует аккуратности.

**Вопрос.** `__dict__` класса vs экземпляра?

**Ответ.** У класса — атрибуты, общие для типа (методы, дескрипторы). У экземпляра — собственные данные; lookup идёт по правилам дескрипторов и MRO, не только в instance dict.

## Лаба

**Цель.** Ромб наследования и слоты.

**Шаги.**
1. Классы A, B(A), C(A), D(B,C) с методом `ping`; напечатайте `D.__mro__` и кто отвечает на `ping` через super-цепочку.
2. Класс с `__slots__ = ("x", "y")`; попробуйте присвоить `z` — поймайте AttributeError.
3. Реализуйте `__repr__` и `__eq__` для точки.
4. Покажите LEGB на вложенной функции с `nonlocal`.

**В группу:** когда multiple inheritance — запах, а когда mixin уместен?

**Готово, если…**
- [ ] Читаете __mro__
- [ ] Объясняете super при diamond
- [ ] Знаете зачем slots

## Схема: MRO diamond

```mermaid
flowchart TD
  D[D] --> B[B]
  D --> C[C]
  B --> A[A]
  C --> A
```

## Тест

### Что такое MRO?

**Ответ:** порядок поиска методов при наследовании

**Пояснение:** C3-линеаризация; Class.__mro__.

### Зачем __slots__?

**Ответ:** ограничить атрибуты, экономия памяти

**Пояснение:** без __dict__ у каждого экземпляра.

### LEGB — расшифровка?

**Ответ:** Local, Enclosing, Global, Builtins

**Пояснение:** порядок поиска имён при чтении.

### super() без аргументов в методе?

**Ответ:** следующий класс в MRO текущего типа

**Пояснение:** не обязательно «родитель» при множественном наследовании.

### _leading underscore convention?

**Ответ:** «internal use», не часть public API

**Пояснение:** __double — name mangling в классе.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>MRO / super() при множественном наследовании</li>
<li>dunder = протоколы языка</li>
<li>slots против произвольного __dict__</li>
</ul>
<h3>Код</h3>
<pre><code>D.__mro__
class P:
    __slots__ = ("x",)
</code></pre>

## Anki

### Front: super() ищет метод где?

Back: в следующем классе по MRO текущего типа

### Front: __repr__ vs __str__?

Back: repr для отладки/однозначности; str для пользователя

### Front: Что в obj.__dict__?

Back: атрибуты экземпляра (если нет slots)

### Front: Множественное наследование — алмаз?

Back: MRO C3 линейализует порядок; super кооперативный

### Front: __slots__ и наследование?

Back: дочерний класс может добавить свои slots; dict может отсутствовать

### Front: globals() vs locals()?

Back: словарь глобальных имён модуля vs локальных в текущем frame

## Итоги

- MRO и dunder — язык «под капотом» ООП
- slots — точечная оптимизация, не default
- Далее: стиль и typing (PY13)

## Ссылки

- [Data model](https://docs.python.org/3/reference/datamodel.html)
- [DEBAGanov — индекс вопросов серии](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- Далее: [PEP8 и typing](/game/learn/py-typing-pep8-static)
