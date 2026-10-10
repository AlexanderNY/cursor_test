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

## Введение

Тесты и отладка на middle — про процесс: arrange-act-assert, фикстуры, когда брать pdb. В источнике сильнее unittest/pdb; в реальных командах чаще pytest — оба должны быть в ответе.

## Раздел: unittest и подход к тестам

`unittest.TestCase`: методы `test_*`, `assertEqual`/`assertRaises`, `setUp`/`tearDown`. Запуск: `python -m unittest`. Хороший unit-тест: быстрый, изолированный, детерминированный, проверяет одно поведение.

Пирамида: много unit, меньше integration, мало e2e. Моки (`unittest.mock`) — для границ (сеть, время), не для всего подряд.

## Раздел: pytest и pdb

pytest: меньше бойлерплейта, `assert` с интроспекцией, **fixtures**, `@pytest.mark.parametrize`. Фикстуры собирают данные/ресурсы; parametrize гоняет один тест на наборе входов — must-have для middle.

Отладка: `pdb` / `breakpoint()` (3.7+). Команды: `n` next, `s` step, `c` continue, `l` list, `p` print, `b` breakpoint. Альтернативы: IDE debugger, логирование вместо print-спама.

Цикл: падение → минимальный воспроизводящий тест → фикс → зелёный прогон.

## Раздел: Частые вопросы с собеседования
**Вопрос.** Unit vs integration test — граница?

**Ответ.** Unit изолирует модуль (моки на границах I/O); integration проверяет связку (БД, HTTP) с реальными или testcontainers. Пирамида: много быстрых unit, меньше integration, мало e2e.

**Вопрос.** Зачем `@pytest.mark.parametrize`?

**Ответ.** Один тест гоняется на наборе входов/ожиданий — меньше копипасты и явная таблица кейсов. На собесе показывает зрелость pytest против голого unittest.

**Вопрос.** Когда мокать, а когда нет?

**Ответ.** Мокайте внешние границы (время, HTTP, SMTP), не внутреннюю логику, которую вы сами тестируете — иначе тест дублирует реализацию. Интеграционный тест без мока ловит контракт с реальным сервисом.

**Вопрос.** `breakpoint()` vs print в отладке?

**Ответ.** `breakpoint()` входит в pdb с контекстом стека, можно шагать и смотреть locals. Print-отладка не масштабируется и остаётся в коде; pdb/IDE debugger — стандарт для middle.

## Лаба

**Цель.** Покрыть функцию pytest + поймать баг в pdb.

**Шаги.**
1. Функция `clamp(x, lo, hi)` с намеренным багом на границе.
2. unittest-тест и pytest-тест с parametrize.
3. Фикстура с временным путём файла (`tmp_path`).
4. Поставьте `breakpoint()` и пройдите баг шагами `n`/`p`.

**В группу:** что вы не мокаете принципиально?

**Готово, если…**
- [ ] Пишете pytest с parametrize
- [ ] Знаете 4 команды pdb
- [ ] Чините через failing test first

## Схема: Красный-зелёный

```mermaid
flowchart LR
  Fail[failing_test] --> Fix[fix_code]
  Fix --> Pass[passing_test]
  Pass --> Refactor[refactor]
  Refactor --> Pass
```

## Тест

### Чем pytest удобнее unittest?

**Ответ:** меньше бойлерплейта, fixtures

**Пояснение:** assert обычный; parametrize масштабируется.

### Зачем parametrize?

**Ответ:** один тест — много вход/ожидание

**Пояснение:** таблица кейсов без копипаста.

### breakpoint() в 3.7+?

**Ответ:** вход в pdb по умолчанию

**Пояснение:** PYTHONBREAKPOINT может подменить debugger.

### unit vs integration тест?

**Ответ:** unit изолирован; integration — несколько компонентов

**Пояснение:** unit быстрее и точнее локализует баг.

### mock/patch зачем?

**Ответ:** изолировать от сети/БД/времени

**Пояснение:** unittest.mock или pytest monkeypatch.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>unit = быстро и изолированно</li>
<li>pytest fixtures + parametrize</li>
<li>pdb: n/s/c/p/l/b</li>
</ul>
<h3>Код</h3>
<pre><code>@pytest.mark.parametrize("x,y", [(1,1),(2,2)])
def test_id(x, y):
    assert x == y
breakpoint()
</code></pre>

## Anki

### Front: setUp в unittest — когда вызывается?

Back: перед каждым test-методом

### Front: Что такое fixture в pytest?

Back: переиспользуемая подготовка данных/ресурсов для тестов

### Front: Команда pdb step into?

Back: s

### Front: pytest.raises зачем?

Back: проверить, что блок выбрасывает ожидаемое исключение

### Front: TDD цикл?

Back: red → green → refactor

### Front: pdb continue?

Back: c — продолжить до следующей breakpoint

## Итоги

- Тесты — часть дизайна, не послесловие
- pytest — де-факто стандарт; unittest знать для собеса/легаси
- Далее senior: дескрипторы (PY17)

## Ссылки

- [unittest](https://docs.python.org/3/library/unittest.html)
- [pytest](https://docs.pytest.org/)
- [pdb](https://docs.python.org/3/library/pdb.html)
- [DEBAGanov — индекс вопросов серии](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- См. также: [pytest CI Git для QA](/game/learn/qa-pytest-ci-git)
- Далее: [Дескрипторы](/game/learn/py-descriptors-metaclasses)
