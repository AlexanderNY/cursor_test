#!/usr/bin/env python3
"""Generate Learn season B (first app) posts and merge into learn_seed.json."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "data" / "learn_seed.json"
START = datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc)

L = lambda slug: f"/game/learn/{slug}"  # noqa: E731


def post(
    *,
    n: int,
    slug: str,
    title: str,
    short: str,
    rubric: str,
    theory: str,
    lab: str,
    cheatsheet: str,
    diagram: str,
    links: list[dict[str, str]],
) -> dict:
    return {
        "slug": slug,
        "episode": f"B{n:02d}",
        "title": title,
        "shortTitle": short,
        "rubricId": rubric,
        "order": 100 + n,
        "theory": theory.strip(),
        "lab": lab.strip(),
        "cheatsheet": cheatsheet.strip(),
        "diagram": diagram.strip(),
        "links": links,
        "theoryFormat": "markdown",
        "labFormat": "markdown",
        "cheatsheetFormat": "markdown",
        "publishedAt": (START + timedelta(days=n - 1)).isoformat().replace("+00:00", "Z"),
    }


def series() -> list[dict]:
    b01 = "b01-karta"
    b02 = "b02-git"
    b03 = "b03-python"
    b04 = "b04-fastapi-health"
    b05 = "b05-api-check"
    b06 = "b06-git-branch"
    b07 = "b07-notes-api"
    b08 = "b08-react-list"
    b09 = "b09-react-form"
    b10 = "b10-docker"
    b11 = "b11-compose"
    b12 = "b12-sklejka"

    return [
        post(
            n=1,
            slug=b01,
            title="Из чего состоит первое приложение",
            short="Карта",
            rubric="architecture",
            theory=f"""
B01 · Карта · первое приложение за серию

Цель сезона B: быстро собрать своё первое приложение — **«Заметки»** (`notes`): API на Python, страница на React, упаковка в Docker. Не весь прод-стенд, а минимальный круг «кнопка → API → список».

Четыре кирпича, которые вы соберёте:

1. **Git** — где живёт код и история ([B02]({L(b02)}), [B06]({L(b06)})).
2. **Python / FastAPI** — HTTP и JSON ([B03]({L(b03)})–[B07]({L(b07)})).
3. **React** — экран поверх готового API ([B08]({L(b08)}), [B09]({L(b09)})).
4. **Docker / Compose** — одинаковый запуск у вас и у друга ([B10]({L(b10)}), [B11]({L(b11)})).

Порядок важен: сначала API можно проверить без UI ([B05]({L(b05)})), потом уже React. Docker — когда код уже отвечает.

Зачем это на 9to18. Площадка про взаимное продвижение проектов: сначала учимся запускать своё, потом показывать его другим. CopyParse — пример «взрослого» стенда, не ДЗ на клон.

Граница. JWT, Kubernetes, Kafka и «красивый дизайн» в сезон B не входят. Финал — [склейка B12]({L(b12)}).

Следующий выпуск: [B02 · Git]({L(b02)}) — репозиторий до первой строки Python.
""",
            lab=f"""
**20 минут.** На бумаге или в `docs/map.md` нарисуйте три коробки: **React**, **API (Python)**, **Git-репозиторий**. Стрелка: «добавить заметку».

**Проверка:** браузер не ходит в базу напрямую; API стоит между UI и данными (пока данные могут быть в памяти — это ок до Docker).

**Дальше:** [B02 · Git]({L(b02)}).
""",
            cheatsheet=f"""
### Сезон B — маршрут

| № | Тема | Ссылка |
|---|------|--------|
| B01 | Карта | этот выпуск |
| B02 | Git init | [открыть]({L(b02)}) |
| B03 | Python / venv | [открыть]({L(b03)}) |
| B04 | FastAPI `/health` | [открыть]({L(b04)}) |
| B05 | Проверка API | [открыть]({L(b05)}) |
| B06 | Git ветка | [открыть]({L(b06)}) |
| B07 | Notes API | [открыть]({L(b07)}) |
| B08 | React список | [открыть]({L(b08)}) |
| B09 | React форма | [открыть]({L(b09)}) |
| B10 | Docker | [открыть]({L(b10)}) |
| B11 | Compose | [открыть]({L(b11)}) |
| B12 | Склейка | [открыть]({L(b12)}) |

### Не делать в B01

- Ставить Minikube «на вырост»
- Писать UI до API
""",
            diagram="flowchart LR\n  User[Браузер] --> UI[React]\n  UI --> API[FastAPI]\n  API --> Mem[(Память_или_БД)]\n  Git[GitHub] -.-> UI\n  Git -.-> API\n  Docker[Compose] -.-> UI\n  Docker -.-> API",
            links=[
                {"label": "B02 · Git →", "href": L(b02)},
                {"label": "Оглавление Learn", "href": "/game/learn"},
                {"label": "CopyParse (референс стенда)", "href": "https://www.copyparse.ru"},
            ],
        ),
        post(
            n=2,
            slug=b02,
            title="Git: репозиторий за 15 минут",
            short="Git",
            rubric="tools",
            theory=f"""
B02 · Git · init, commit, .gitignore

Код на Рабочем столе без истории — черновик. Git фиксирует *что* изменилось. GitHub — место, куда потом положите Docker-инструкции из [B11]({L(b11)}).

Сквозной проект сезона: репозиторий **`notes`**.

### 1. Создайте repo

На GitHub: New repository → `notes` (private ок) → **без** README, если делаете `git init` локально.

```bash
mkdir notes && cd notes
git init
git branch -M main
```

### 2. .gitignore до первого commit

Иначе `venv/` и `.env` уедут в историю навсегда (секреты понадобятся ближе к [B10]({L(b10)})).

```
.env
venv/
.venv/
__pycache__/
*.pyc
node_modules/
dist/
.idea/
.vscode/
*.pem
```

### 3. Первый commit

```bash
# README: что за сервис (заметки), для кого, стек позже
git add .gitignore README.md
git status
git commit -m "init: notes app, gitignore"
```

Карта слоёв из [B01]({L(b01)}) можно положить в `docs/map.md` вторым commit — или оставить на [B06]({L(b06)}).

Зачем это дальше. В [B03]({L(b03)}) в этот же repo появится Python. В [B08]({L(b08)}) — папка `web/`. Один репозиторий на всё приложение.

Граница. Ветки и PR — в [B06]({L(b06)}). Сейчас достаточно `main` + понятный commit.

Следующий: [B03 · Python]({L(b03)}).
""",
            lab=f"""
**25 минут.**

1. Создайте GitHub-репозиторий `notes` (без README).
2. Локально: `git init`, `.gitignore` из теории, `README.md` на 3 строки.
3. Commit `init: notes app, gitignore` и `git push -u origin main`.

**В группу / себе:** ссылка на репозиторий.

**Проверка:** в Files на GitHub нет `venv/`; в README есть слово «заметки».

**Дальше:** [B03 · Python]({L(b03)}). Назад: [B01]({L(b01)}).
""",
            cheatsheet=f"""
### Happy path

```bash
git init && git branch -M main
git add .gitignore README.md
git commit -m "init: notes app, gitignore"
git remote add origin https://github.com/<you>/notes.git
git push -u origin main
```

### Связи

- Карта приложения: [B01]({L(b01)})
- Ветка и PR: [B06]({L(b06)})
""",
            diagram="flowchart LR\n  Local[локально] --> Init[git_init]\n  Init --> Ignore[gitignore]\n  Ignore --> Commit[commit]\n  Commit --> Remote[GitHub]",
            links=[
                {"label": "← B01 · Карта", "href": L(b01)},
                {"label": "B03 · Python →", "href": L(b03)},
                {"label": "B06 · Ветка Git", "href": L(b06)},
                {"label": "Pro Git", "href": "https://git-scm.com/book/ru/v2"},
            ],
        ),
        post(
            n=3,
            slug=b03,
            title="Python: venv и первая команда",
            short="Python",
            rubric="api",
            theory=f"""
B03 · Python · окружение

API сезона будет на **Python 3.12+**. Сначала — изолированное окружение, чтобы пакеты FastAPI из [B04]({L(b04)}) не смешались с системным Python.

Работайте **внутри** репозитория `notes` из [B02]({L(b02)}).

### 1. Проверьте Python

```bash
python --version
# или: python3 --version
```

Нужен 3.11+ (лучше 3.12).

### 2. venv

```bash
cd notes
python -m venv .venv
# Windows PowerShell:
.\\.venv\\Scripts\\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
python -m pip install --upgrade pip
```

Папка `.venv/` уже в `.gitignore` из B02 — не коммитьте её.

### 3. Проверка

```bash
python -c "print('notes ok')"
```

Граница. Пока не ставьте FastAPI — это [B04]({L(b04)}). Не ставьте глобально без venv.

Следующий: [B04 · FastAPI `/health`]({L(b04)}).
""",
            lab=f"""
**20 минут.** В репо `notes`:

1. Создайте и активируйте `.venv`.
2. Выполните `python -c "print('notes ok')"`.
3. Commit не нужен (venv не в git). Обновите README одной строкой: «Python 3.12, venv».

**Проверка:** в терминале видно `(.venv)`; `python -c` печатает `notes ok`.

**Дальше:** [B04]({L(b04)}). Назад: [B02]({L(b02)}).
""",
            cheatsheet=f"""
```bash
python -m venv .venv
# Windows: .\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -c "print('notes ok')"
```

Не коммитить: `.venv/`, `__pycache__/`.

Дальше: [B04 FastAPI]({L(b04)}).
""",
            diagram="flowchart LR\n  Py[Python] --> Venv[.venv]\n  Venv --> Pip[pip]\n  Pip --> App[код_notes]",
            links=[
                {"label": "← B02 · Git", "href": L(b02)},
                {"label": "B04 · FastAPI →", "href": L(b04)},
                {"label": "venv — docs.python.org", "href": "https://docs.python.org/3/library/venv.html"},
            ],
        ),
        post(
            n=4,
            slug=b04,
            title="FastAPI: первый /health",
            short="FastAPI",
            rubric="api",
            theory=f"""
B04 · FastAPI · `/health`

API начинается с контракта: путь, ответ, код. FastAPI это фиксирует типами и сразу даёт Swagger на `/docs`.

В репо `notes` (venv из [B03]({L(b03)})):

```bash
pip install "fastapi[standard]"
```

Минимальный `api/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="notes")

@app.get("/health")
def health():
    return {{"status": "ok"}}
```

Запуск:

```bash
uvicorn api.main:app --reload --port 8000
```

Откройте `http://127.0.0.1:8000/health` и `http://127.0.0.1:8000/docs`.

Зачем без React. В [B05]({L(b05)}) научитесь проверять API до UI. В [B07]({L(b07)}) добавите заметки. В [B10]({L(b10)}) этот же процесс попадёт в Docker.

Граница. Без БД, JWT и CORS-танцев. Один процесс, одна ручка.

Следующий: [B05 · проверка API]({L(b05)}).
""",
            lab=f"""
**30 минут.**

1. `pip install "fastapi[standard]"` в venv.
2. Файл `api/main.py` с `GET /health`.
3. Запустите uvicorn, откройте `/docs`.
4. Commit: `feat: fastapi health endpoint`.

**Проверка:** `/health` → `{{"status":"ok"}}`; в `/docs` видна ручка.

**Дальше:** [B05]({L(b05)}). Назад: [B03]({L(b03)}).
""",
            cheatsheet=f"""
```bash
pip install "fastapi[standard]"
uvicorn api.main:app --reload --port 8000
```

| URL | Ожидание |
|-----|----------|
| `/health` | `{{"status":"ok"}}` |
| `/docs` | Swagger UI |

Связи: [B05]({L(b05)}), [B07]({L(b07)}), [B10]({L(b10)}).
""",
            diagram="flowchart LR\n  Client[Клиент] --> Health[GET_/health]\n  Health --> App[FastAPI]\n  App --> JSON[status_ok]",
            links=[
                {"label": "← B03 · Python", "href": L(b03)},
                {"label": "B05 · Проверка API →", "href": L(b05)},
                {"label": "B07 · Notes API", "href": L(b07)},
                {"label": "FastAPI First Steps", "href": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
            ],
        ),
        post(
            n=5,
            slug=b05,
            title="Как проверить API без React",
            short="Проверка API",
            rubric="tools",
            theory=f"""
B05 · Проверка · curl и браузер

Пока нет React ([B08]({L(b08)})), API из [B04]({L(b04)}) уже можно проверить тремя способами.

### 1. Браузер

`http://127.0.0.1:8000/health` — для GET достаточно.

### 2. Swagger `/docs`

Кнопка Try it out → Execute. Удобно видеть схему ответа.

### 3. curl / PowerShell

```bash
curl http://127.0.0.1:8000/health
```

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Зачем это. Когда в [B07]({L(b07)}) появится `POST /notes`, вы сначала проверите его здесь, и только потом повесите кнопку в [B09]({L(b09)}). Иначе отладка «не работает форма» смешивает UI и API.

Граница. Insomnia/Postman — по желанию; curl достаточно.

Следующий: [B06 · Git ветка]({L(b06)}) — зафиксировать прогресс до усложнения API.
""",
            lab=f"""
**15 минут.** При запущенном uvicorn из [B04]({L(b04)}):

1. Откройте `/health` в браузере.
2. Выполните curl или `Invoke-RestMethod`.
3. В `/docs` нажмите Execute на `/health`.

**Проверка:** три способа показывают `status: ok`.

**Дальше:** [B06]({L(b06)}). Назад: [B04]({L(b04)}).
""",
            cheatsheet=f"""
```bash
curl http://127.0.0.1:8000/health
```

Порядок отладки: **API → потом UI**. См. [B09]({L(b09)}).
""",
            diagram="flowchart LR\n  Browser[Браузер] --> Health\n  Curl[curl] --> Health\n  Docs[Swagger] --> Health\n  Health[GET_/health]",
            links=[
                {"label": "← B04 · FastAPI", "href": L(b04)},
                {"label": "B06 · Git ветка →", "href": L(b06)},
                {"label": "B07 · Notes API", "href": L(b07)},
            ],
        ),
        post(
            n=6,
            slug=b06,
            title="Git: ветка и понятный README",
            short="Git ветка",
            rubric="tools",
            theory=f"""
B06 · Git · ветка и README

Перед `POST /notes` ([B07]({L(b07)})) закрепим привычку: лаба не пишется прямо в `main`.

```bash
git switch -c b06-readme
# обновите README: как поднять venv и uvicorn (команды из B03–B04)
git add README.md
git commit -m "docs: how to run health API"
git push -u origin b06-readme
```

На GitHub: Pull Request `b06-readme` → `main`. Смотрите **Files changed**.

README минимум:

1. Что это (`notes`).
2. Как создать venv ([B03]({L(b03)})).
3. Как запустить `uvicorn` ([B04]({L(b04)})).

Позже в [B12]({L(b12)}) добавите Compose.

Граница. Rebase и monorepo-тулинг не нужны. Ветка + PR + читаемый commit.

Следующий: [B07 · Notes API]({L(b07)}).
""",
            lab=f"""
**25 минут.**

1. Ветка `b06-readme`, обновите README командами запуска.
2. Push и PR в `main`.
3. Merge после самопроверки диффа.

**Проверка:** в PR нет `.venv`; commit message не `fix`.

**Дальше:** [B07]({L(b07)}). Назад: [B02]({L(b02)}), [B05]({L(b05)}).
""",
            cheatsheet=f"""
```bash
git switch -c b06-readme
git add README.md
git commit -m "docs: how to run health API"
git push -u origin b06-readme
```

Связи: [B02]({L(b02)}), финал README — [B12]({L(b12)}).
""",
            diagram="flowchart LR\n  Main[main] --> Branch[b06_readme]\n  Branch --> PR[Pull_Request]\n  PR --> Main",
            links=[
                {"label": "← B05 · Проверка API", "href": L(b05)},
                {"label": "B07 · Notes API →", "href": L(b07)},
                {"label": "B02 · Git init", "href": L(b02)},
                {"label": "GitHub Flow", "href": "https://docs.github.com/ru/get-started/using-github/github-flow"},
            ],
        ),
        post(
            n=7,
            slug=b07,
            title="Notes API: список и создание",
            short="Notes API",
            rubric="api",
            theory=f"""
B07 · FastAPI · заметки в памяти

Расширяем [B04]({L(b04)}): ресурс заметок без БД. React в [B08]({L(b08)})–[B09]({L(b09)}) будет бить именно сюда.

Пример моделей и ручек в `api/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="notes")
_notes: list[dict] = []
_next_id = 1

class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)

class Note(NoteIn):
    id: int

@app.get("/health")
def health():
    return {{"status": "ok"}}

@app.get("/notes", response_model=list[Note])
def list_notes():
    return _notes

@app.post("/notes", response_model=Note)
def create_note(body: NoteIn):
    global _next_id
    note = {{"id": _next_id, "title": body.title}}
    _next_id += 1
    _notes.append(note)
    return note
```

Проверьте через приёмы [B05]({L(b05)}):

```bash
curl -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d "{{\\"title\\":\\"первая\\"}}"
curl http://127.0.0.1:8000/notes
```

Граница. Postgres подождёт сезона S01. После рестарта uvicorn список обнулится — это ожидаемо.

Следующий: [B08 · React список]({L(b08)}).
""",
            lab=f"""
**40 минут.** В ветке `b07-notes-api`:

1. Добавьте `GET/POST /notes` как в теории (или эквивалент).
2. Проверьте curl/Swagger.
3. Commit + PR.

**Проверка:** после POST список на GET содержит новую заметку; `/health` жив.

**Дальше:** [B08]({L(b08)}). Назад: [B04]({L(b04)}), [B05]({L(b05)}).
""",
            cheatsheet=f"""
| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/health` | живость |
| GET | `/notes` | список |
| POST | `/notes` | создать |

Отладка: [B05]({L(b05)}). UI: [B08]({L(b08)}), [B09]({L(b09)}).
""",
            diagram="flowchart LR\n  Client --> Post[POST_/notes]\n  Client --> Get[GET_/notes]\n  Post --> Mem[(list_in_memory)]\n  Get --> Mem",
            links=[
                {"label": "← B06 · Git ветка", "href": L(b06)},
                {"label": "B08 · React список →", "href": L(b08)},
                {"label": "B05 · Проверка API", "href": L(b05)},
                {"label": "Pydantic / Body", "href": "https://fastapi.tiangolo.com/tutorial/body/"},
            ],
        ),
        post(
            n=8,
            slug=b08,
            title="React: список заметок с API",
            short="React список",
            rubric="frontend",
            theory=f"""
B08 · React · список

UI появляется **после** рабочего API ([B07]({L(b07)})). В том же репо `notes`:

```bash
npm create vite@latest web -- --template react-ts
cd web
npm install
npm run dev
```

На странице: `fetch("http://127.0.0.1:8000/notes")` → показать `title` списком.

CORS: в FastAPI добавьте (временно для учёбы):

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Зачем так. В [B05]({L(b05)}) вы уже знаете, что API отвечает; если список пустой — сначала curl, потом React.

Следующий: [B09 · форма]({L(b09)}).
""",
            lab=f"""
**40 минут.**

1. Создайте Vite React-TS в `web/`.
2. На главной загрузите `/notes` и отрисуйте список.
3. Включите CORS на API, commit оба изменения.

**Проверка:** при запущенных API и `npm run dev` видны заметки, созданные через curl.

**Дальше:** [B09]({L(b09)}). Назад: [B07]({L(b07)}).
""",
            cheatsheet=f"""
```bash
npm create vite@latest web -- --template react-ts
cd web && npm install && npm run dev
```

Порядок отладки: curl ([B05]({L(b05)})) → React.

Форма: [B09]({L(b09)}).
""",
            diagram="flowchart LR\n  Page[React] --> Fetch[fetch_/notes]\n  Fetch --> API[FastAPI]\n  API --> List[ul_li]",
            links=[
                {"label": "← B07 · Notes API", "href": L(b07)},
                {"label": "B09 · React форма →", "href": L(b09)},
                {"label": "Vite Guide", "href": "https://vite.dev/guide/"},
            ],
        ),
        post(
            n=9,
            slug=b09,
            title="React: форма «добавить заметку»",
            short="React форма",
            rubric="frontend",
            theory=f"""
B09 · React · POST из формы

Замыкаем круг: поле ввода → `POST /notes` → обновить список ([B07]({L(b07)}), [B08]({L(b08)})).

```ts
await fetch("http://127.0.0.1:8000/notes", {{
  method: "POST",
  headers: {{ "Content-Type": "application/json" }},
  body: JSON.stringify({{ title }}),
}})
```

После успеха — снова `GET /notes` или добавьте ответ POST в локальный state.

Это и есть «первое приложение» до Docker: человек жмёт кнопку, данные появляются в списке.

Дальше упакуем API в образ ([B10]({L(b10)})) и поднимем Compose ([B11]({L(b11)})).

Граница. Авторизация, редактирование, удаление — не в сезон B.
""",
            lab=f"""
**40 минут.**

1. Форма с `title`, кнопка «Добавить».
2. POST на API, обновление списка без перезагрузки страницы.
3. Commit + короткий скрин в PR (по желанию).

**Проверка:** заметка из UI видна и в curl `GET /notes`.

**Дальше:** [B10]({L(b10)}). Назад: [B08]({L(b08)}).
""",
            cheatsheet=f"""
Круг: `форма → POST /notes → GET /notes → ul`.

Связи: [B07]({L(b07)}), [B08]({L(b08)}), Docker: [B10]({L(b10)}).
""",
            diagram="flowchart LR\n  Form[форма] --> Post[POST_/notes]\n  Post --> API[FastAPI]\n  API --> Refresh[GET_/notes]\n  Refresh --> UI[список]",
            links=[
                {"label": "← B08 · React список", "href": L(b08)},
                {"label": "B10 · Docker →", "href": L(b10)},
                {"label": "B07 · Notes API", "href": L(b07)},
            ],
        ),
        post(
            n=10,
            slug=b10,
            title="Docker: образ API",
            short="Docker",
            rubric="tools",
            theory=f"""
B10 · Docker · образ FastAPI

Друг без вашего venv должен поднять тот же API из [B07]({L(b07)}). Для этого — образ.

`api/requirements.txt`:

```
fastapi[standard]==0.115.6
```

`api/Dockerfile` (пример):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Если код в `api/main.py` и контекст сборки — папка `api/`:

```bash
cd api
docker build -t notes-api .
docker run --rm -p 8000:8000 notes-api
```

Проверка как в [B05]({L(b05)}): `curl localhost:8000/health`.

Граница. UI в образ пока не кладём — в [B11]({L(b11)}) решим через Compose (API + dev UI или статика).

Следующий: [B11 · Compose]({L(b11)}).
""",
            lab=f"""
**40 минут.**

1. `requirements.txt` + `Dockerfile` для API.
2. `docker build` и `docker run -p 8000:8000`.
3. curl `/health` и `/notes`.
4. Commit.

**Проверка:** API отвечает из контейнера без локального venv.

**Дальше:** [B11]({L(b11)}). Назад: [B07]({L(b07)}), [B04]({L(b04)}).
""",
            cheatsheet=f"""
```bash
docker build -t notes-api .
docker run --rm -p 8000:8000 notes-api
```

Не коммитить секреты. Compose: [B11]({L(b11)}).
""",
            diagram="flowchart LR\n  Dockerfile --> Build[docker_build]\n  Build --> Image[notes_api]\n  Image --> Run[docker_run_:8000]",
            links=[
                {"label": "← B09 · React форма", "href": L(b09)},
                {"label": "B11 · Compose →", "href": L(b11)},
                {"label": "B05 · Проверка API", "href": L(b05)},
                {"label": "Docker Get Started", "href": "https://docs.docker.com/get-started/"},
            ],
        ),
        post(
            n=11,
            slug=b11,
            title="Compose: поднять приложение одной командой",
            short="Compose",
            rubric="tools",
            theory=f"""
B11 · Compose · API (+ UI)

`docker-compose.yml` в корне `notes`:

```yaml
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
```

Запуск:

```bash
docker compose up --build
```

Опционально добавьте сервис `web` (nginx со статикой после `npm run build`) или оставьте UI на `npm run dev` против `localhost:8000` — для учёбы оба варианта ок. Главное: **API поднимается одной командой**, как обещали в [B01]({L(b01)}).

Проверка: [B05]({L(b05)}) + форма из [B09]({L(b09)}).

Следующий: [B12 · склейка]({L(b12)}) — чеклист и README для портфолио / взаимного продвижения на 9to18.
""",
            lab=f"""
**40 минут.**

1. `docker-compose.yml` с сервисом `api`.
2. `docker compose up --build`, curl `/health`.
3. Обновите README секцией Compose.
4. Commit.

**Проверка:** на чистой машине с Docker (без ручного venv) API отвечает.

**Дальше:** [B12]({L(b12)}). Назад: [B10]({L(b10)}).
""",
            cheatsheet=f"""
```bash
docker compose up --build
```

Связи: [B10]({L(b10)}), финал: [B12]({L(b12)}).
""",
            diagram="flowchart LR\n  Compose[compose_up] --> API[api_:8000]\n  Compose -.-> Web[web_опционально]\n  User[браузер] --> Web\n  User --> API",
            links=[
                {"label": "← B10 · Docker", "href": L(b10)},
                {"label": "B12 · Склейка →", "href": L(b12)},
                {"label": "B01 · Карта", "href": L(b01)},
                {"label": "Compose spec", "href": "https://docs.docker.com/compose/"},
            ],
        ),
        post(
            n=12,
            slug=b12,
            title="Склейка: что должно получиться",
            short="Склейка",
            rubric="architecture",
            theory=f"""
B12 · Склейка · чеклист первого приложения

Вы прошли круг сезона B:

1. Карта — [B01]({L(b01)})
2. Git — [B02]({L(b02)}), [B06]({L(b06)})
3. Python / FastAPI — [B03]({L(b03)})–[B07]({L(b07)})
4. Проверка без UI — [B05]({L(b05)})
5. React — [B08]({L(b08)}), [B09]({L(b09)})
6. Docker / Compose — [B10]({L(b10)}), [B11]({L(b11)})

### Чеклист «готово»

- [ ] Репозиторий на GitHub, README с командами
- [ ] `GET /health` и `GET/POST /notes`
- [ ] React: список + форма
- [ ] `docker compose up --build` поднимает API
- [ ] В git нет `.venv`, `node_modules`, `.env` с секретами

### Что писать в README для продвижения

На 9to18 взаимное продвижение начинается с понятного «как запустить за 5 минут». Три команды в README важнее длинного манифеста.

### Куда дальше

Когда будете готовы к БД, JWT и Minikube — смотрите сезон S01 на Learn (Postgres, Docker «взрослее», k8s). Сезон B сознательно короче.

Следующий шаг вне серии: покажите `notes` другу или вынесите ссылку на репо в спотлайт сообщества.
""",
            lab=f"""
**30 минут.** Пройдите чеклист из теории по своему репо. Допишите README, если чего-то нет.

**Проверка:** человек с Docker Desktop поднимает API по README без голосовых подсказок.

**Назад по серии:** [B01]({L(b01)}) … [B11]({L(b11)}). Оглавление: [/game/learn](/game/learn).
""",
            cheatsheet=f"""
### Маршрут сезона B

[B01]({L(b01)}) → [B02]({L(b02)}) → [B03]({L(b03)}) → [B04]({L(b04)}) → [B05]({L(b05)}) → [B06]({L(b06)}) → [B07]({L(b07)}) → [B08]({L(b08)}) → [B09]({L(b09)}) → [B10]({L(b10)}) → [B11]({L(b11)}) → **B12**

### Готово, если…

- API + React + Compose
- README на 5 минут запуска
- Без секретов в git
""",
            diagram="flowchart LR\n  B01 --> B02 --> B03 --> B04 --> B05 --> B06\n  B06 --> B07 --> B08 --> B09 --> B10 --> B11 --> B12",
            links=[
                {"label": "← B11 · Compose", "href": L(b11)},
                {"label": "B01 · Карта (старт)", "href": L(b01)},
                {"label": "Оглавление Learn", "href": "/game/learn"},
                {"label": "Сезон S01 · слои (продолжение)", "href": "/game/learn/s01e01-sloi"},
            ],
        ),
    ]


def main() -> None:
    existing = json.loads(SEED.read_text(encoding="utf-8"))
    if not isinstance(existing, list):
        raise SystemExit("seed is not a list")
    by_slug = {str(item.get("slug")): item for item in existing if isinstance(item, dict)}
    for item in series():
        by_slug[item["slug"]] = item
    # stable: keep non-B order, then B by order field
    merged = sorted(by_slug.values(), key=lambda x: (int(x.get("order") or 0), str(x.get("slug"))))
    SEED.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    b_count = sum(1 for x in merged if str(x.get("episode", "")).startswith("B"))
    print(f"wrote {SEED} total={len(merged)} season_b={b_count}")


if __name__ == "__main__":
    main()
