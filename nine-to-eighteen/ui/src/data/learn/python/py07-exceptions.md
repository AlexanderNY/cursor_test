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

## Введение

Ошибки на собесе проверяют не только синтаксис `try`, но понимание `else`/`finally`, иерархии и того, что будет, если исключение не поймали. Собираем аккуратную модель обработки сбоев.

## Раздел: try / except / else / finally

```python
try:
    risky()
except ValueError as exc:
    handle(exc)
else:
    # только если исключения не было
    after_success()
finally:
    # всегда: освободить ресурс / залогировать завершение
    cleanup()
```

`raise` пробрасывает или создаёт исключение. `raise ... from exc` сохраняет цепочку причин. Ловите **конкретные** типы, не голый `except:` (он перехватит и `KeyboardInterrupt` в плохих вариантах со `BaseException`).

`NotImplementedError` — маркер «метод должен реализовать подкласс», не путать с `NotImplemented` (для операторов).

## Раздел: Иерархия и свои классы

База пользовательских ошибок — обычно `Exception` (не `BaseException`). Деление на ноль → `ZeroDivisionError` (под `ArithmeticError`). Runtime errors — ошибки во время исполнения vs SyntaxError на этапе разбора.

Свой тип:

```python
class DomainError(Exception):
    """Бизнес-ошибка домена."""
```

Если исключение не обработано, оно летит вверх по стеку и завершает поток/программу с traceback. `finally` выполняется даже при пробросе дальше — поэтому его любят для закрытия ресурсов (рядом с `with`).

## Раздел: Частые вопросы с собеседования
**Вопрос.** Чем `with` лучше `try/finally` для файла?

**Ответ.** Оба могут закрыть ресурс, но `with` инкапсулирует протокол `__enter__`/`__exit__` и короче. Для нескольких ресурсов — `with open(...) as f, open(...) as g`. Обработку доменных ошибок всё равно проектируют через `except`.

**Вопрос.** Почему не ловить голый `except:`?

**Ответ.** Перехватывается слишком много, включая `KeyboardInterrupt` и `SystemExit` в плохих вариантах. Ловите конкретные типы или `Exception`, если осознанно; логируйте и пробрасывайте неожиданное.

**Вопрос.** Зачем `raise ... from exc`?

**Ответ.** Сохраняет цепочку причин в traceback (`__cause__`), полезно при обёртке низкоуровневой ошибки в доменную. Без `from` в Python 3 есть implicit context (`__context__`), но явное `from` яснее для читателя.

**Вопрос.** `else` в блоке `try` — когда выполняется?

**Ответ.** Только если в `try` не было исключения — удобно для кода, который должен идти после успешного risky, но не смешиваться с cleanup в `finally`.

## Лаба

**Цель.** Парсер числа с доменными ошибками и корректным finally.

**Шаги.**
1. `parse_positive(text)` → int > 0 или `ValueError` / свой `ParseError`.
2. Оберните вызов: except → сообщение, else → print ok, finally → print done.
3. Покажите разницу: поймали ошибку vs не поймали (traceback).
4. Добавьте `raise ParseError(...) from exc` при обёртке низкоуровневой ошибки.

Заготовка try / else / finally:

```python
class ParseError(ValueError):
    pass

def parse_positive(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise ParseError(f"not an int: {text!r}") from exc
    if value <= 0:
        raise ParseError(f"need > 0, got {value}")
    return value

for sample in ("12", "0", "x"):
    try:
        n = parse_positive(sample)
    except ParseError as exc:
        print(f"{sample!r}: caught", exc)
    else:
        print(f"{sample!r}: ok", n)
    finally:
        print(f"{sample!r}: done")
```

**В группу:** когда лучше вернуть `None`/Result, а когда raise?

**Готово, если…**
- [ ] Объясняете else и finally
- [ ] Ловите конкретные типы
- [ ] Пишете свой Exception-класс

## Схема: Поток исключения

```mermaid
flowchart TD
  Try[try_body] -->|ok| Else[else_block]
  Try -->|raise| Except[matching_except]
  Except --> Finally[finally]
  Else --> Finally
  Except -->|re_raise| Up[propagate]
  Finally --> Up
  Finally --> Done[continue]
```

## Тест

### Когда выполняется else в try?

**Ответ:** если в try не было исключения

**Пояснение:** else не связан с except как «иначе ошибка»; это «успешный try».

### Зачем finally?

**Ответ:** код очистки, который выполнится всегда

**Пояснение:** и при успехе, и при ошибке, и при return из try.

### Что будет, если исключение не поймать?

**Ответ:** проброс вверх и traceback

**Пояснение:** пока кто-то выше не обработает или интерпретатор не завершит поток.

### except Exception vs except BaseException?

**Ответ:** BaseException шире — SystemExit, KeyboardInterrupt

**Пояснение:** прикладной код обычно ловит Exception, не глотая Ctrl+C.

### raise ValueError("msg") from e?

**Ответ:** цепочка __cause__ для отладки

**Пояснение:** явная причина; без from теряется контекст обёртки.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>try/except/else/finally + raise</li>
<li>ловить конкретно; свои ошибки от Exception</li>
<li>finally ≈ гарантия cleanup (with ещё лучше для ресурсов)</li>
</ul>
<h3>Код</h3>
<pre><code>try:
    ...
except ValueError as e:
    raise DomainError("bad") from e
finally:
    cleanup()
</code></pre>

## Anki

### Front: BaseException vs Exception?

Back: BaseException включает SystemExit/KeyboardInterrupt; прикладной код обычно ловит Exception

### Front: NotImplementedError — когда?

Back: абстрактный/нереализованный метод в базовом классе

### Front: raise X from e — зачем?

Back: сохранить причинно-следственную цепочку исключений

### Front: except Exception as e: pass — антипаттерн?

Back: да — глотает все ошибки без логирования и маскирует баги

### Front: Свой класс ошибок — от чего наследовать?

Back: от Exception (или его подкласса), не от BaseException

### Front: else в try выполнится при return в try?

Back: нет — return из try пропускает else

## Итоги

- Корректная обработка ошибок — признак зрелого junior
- else/finally часто путают — закрепите схемой
- Дальше — stdlib re/json/copy (PY08)

## Ссылки

- [Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
- [DEBAGanov — индекс вопросов серии](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- Далее: [re / json / copy](/game/learn/py-stdlib-re-json-copy)
