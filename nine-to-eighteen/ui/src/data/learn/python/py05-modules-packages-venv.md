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

## Введение

«Как вы организуете код и зависимости?» — стандарт junior/middle. Нужно чётко разделять модуль и пакет, понимать `venv`, `pip`, wheels и зачем `__name__ == "__main__"`.

## Раздел: Модули и пакеты

Модуль — файл `.py` (или скомпилированное расширение). Пакет — каталог с модулями (исторически с `__init__.py`; namespace packages — без него). Импорт ищет по `sys.path`; `.pth` файлы могут дополнять пути. Stdlib лежит в установке Python (`sys.prefix` / `Lib`).

`__name__`: при прямом запуске равен `"__main__"`, при импорте — имя модуля. Паттерн:

```python
def main():
    ...

if __name__ == "__main__":
    main()
```

Перезагрузка: `importlib.reload` (осторожно в проде). `__pycache__` / `.pyc` — кеш bytecode. Импортировать «весь модуль» vs `from x import y` — вкус и риск загрязнения namespace; круговые импорты лечат рефакторингом.

## Раздел: venv, pip, wheels

Виртуальное окружение изолирует зависимости проекта (`python -m venv .venv`). Менеджеры: `pip`, иногда poetry/uv/pipenv — идея одна: зафиксировать версии. **Wheel** (`.whl`) — современный бинарный/готовый дистрибутив; **egg** — устаревший формат.

Транзитивные зависимости тянет resolver pip; конфликты версий — через constraints/`pip check`. Упаковка своего кода: `pyproject.toml` / setuptools, сборка wheel. Переменные окружения интерпретатора (`PYTHONPATH`, `PYTHONOPTIMIZE`) влияют на поиск модулей и `-O`.

## Раздел: Частые вопросы с собеседования
**Вопрос.** Зачем `venv`, если Python уже установлен?

**Ответ.** Изолирует версии зависимостей проекта от системного Python и других проектов. Без venv `pip install` ломает глобальное окружение; в CI и проде фиксируют requirements/lock и собирают образ с тем же набором пакетов.

**Вопрос.** Wheel против sdist — в чём разница?

**Ответ.** Wheel — готовый бинарный или platform-specific дистрибутив, быстрая установка без компиляции на машине. sdist — архив исходников, pip может собрать на месте. Для продакшена предпочитают wheel там, где доступен.

**Вопрос.** Что такое `if __name__ == "__main__"`?

**Ответ.** Модуль при прямом запуске получает `__name__ == "__main__"`, при импорте — имя модуля. Блок под guard запускает CLI/демо только при исполнении файла, а не при импорте как библиотеки.

**Вопрос.** Как бороться с circular import на собесе?

**Ответ.** Рефакторинг: вынести общее в третий модуль, отложенный импорт внутри функции, или перестроить зависимости. «Перезагрузить importlib» — не решение для прода, только для REPL.

## Лаба

**Цель.** Мини-пакет с venv и точкой входа.

**Шаги.**
1. `python -m venv .venv`, активируйте, `pip install requests` (или любой лёгкий пакет).
2. Структура `mylib/__init__.py`, `mylib/util.py`, скрипт `run.py` с guard `__main__`.
3. Запустите как скрипт и как `python -c "import mylib"`.
4. `pip freeze > requirements.txt`; объясните, чем freeze отличается от «прямых» зависимостей.

Модель `__all__` / публичных имён (venv делайте локально; в [Code](/game/code) — только идея экспорта):

```python
fake_module = {
    "helper": lambda: "ok",
    "_private": 1,
    "__dunder__": 2,
    "util": "public",
}

def public_names(mapping: dict[str, object]) -> list[str]:
    return sorted(name for name in mapping if not name.startswith("_"))

print("public:", public_names(fake_module))
print("__name__ in this run:", __name__)
```

**В группу:** назовите 3 модуля stdlib, которыми пользуетесь ежедневно.

**Готово, если…**
- [ ] Отличаете module и package
- [ ] Поднимаете venv без путаницы с системным Python
- [ ] Объясняете wheel vs «поставить из исходников»

## Схема: Поиск импорта

```mermaid
flowchart TD
  Import[import_name] --> Path[sys_path]
  Path --> Stdlib[stdlib]
  Path --> VenvSite[venv_site_packages]
  Path --> Cwd[project_dirs]
  VenvSite --> Wheel[installed_wheels]
```

## Тест

### Чем пакет отличается от модуля?

**Ответ:** пакет — каталог модулей; модуль — единица import

**Пояснение:** пакет группирует API; модуль — конкретный `.py` или extension.

### Зачем virtualenv?

**Ответ:** изолировать зависимости проекта

**Пояснение:** разные проекты не ломают друг другу версии пакетов.

### Что такое wheel?

**Ответ:** бинарный/готовый дистрибутив для pip

**Пояснение:** быстрая установка; eggs устарели.

### Где Python ищет модули при import?

**Ответ:** по sys.path

**Пояснение:** stdlib, site-packages venv, cwd, PYTHONPATH.

### import pkg vs from pkg import name?

**Ответ:** первый загружает модуль; второй — имя в локальную область

**Пояснение:** from import * засоряет namespace — избегайте в продакшене.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>module = единица импорта; package = набор модулей</li>
<li>venv + pip + requirements/lock</li>
<li>__name__ == "__main__" для CLI-точки входа</li>
</ul>
<h3>Команды</h3>
<pre><code>python -m venv .venv
pip install -r requirements.txt
python -m pip install build
</code></pre>

## Anki

### Front: Где Python ищет модули?

Back: по элементам sys.path (stdlib, site-packages, cwd/PYTHONPATH)

### Front: Что в __pycache__?

Back: скомпилированный bytecode (.pyc) для ускорения последующих импортов

### Front: Зачем if __name__ == "__main__"?

Back: код запускается только при прямом старте файла, не при импорте

### Front: Чем pip install -r отличается от pip install pkg?

Back: -r ставит фиксированный набор версий из файла requirements

### Front: Зачем файл __init__.py в пакете?

Back: помечает каталог как пакет (namespace packages — отдельный случай в PEP 420)

### Front: python -m module зачем?

Back: запуск модуля как скрипта с корректным sys.path

## Итоги

- Организация кода и окружения — база любого проекта
- venv обязателен в ответе junior
- Дальше — ООП (PY06)

## Ссылки

- [Modules](https://docs.python.org/3/tutorial/modules.html)
- [Installing Packages — packaging.python.org](https://packaging.python.org/en/latest/tutorials/installing-packages/)
- [Installing Packages — packaging.python.org](https://packaging.python.org/en/latest/tutorials/installing-packages/)
- [venv](https://docs.python.org/3/library/venv.html)
- [DEBAGanov — индекс вопросов серии](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md)
- Learn | /game/learn
- Далее: [ООП база](/game/learn/py-oop-basics)
