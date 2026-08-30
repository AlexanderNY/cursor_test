# Сезон B · Первое приложение (Git, Python, React, Docker)

Черновики и канон для Learn на **9to18.ru**. Обращение на **вы**.

Сквозной проект: **`notes`** (заметки) — API + React + Docker Compose.

На сайте выпуски живут в `core/data/learn_seed.json` (коды `B01`…`B12`, slug `b01-karta` … `b12-sklejka`). Внутри текстов и блока «Ссылки» — пути `/game/learn/...` (перелинковка SPA).

## Порядок выпуска

| Код | Slug | Тема |
|-----|------|------|
| B01 | `b01-karta` | Карта первого приложения |
| B02 | `b02-git` | Git: init и .gitignore |
| B03 | `b03-python` | Python / venv |
| B04 | `b04-fastapi-health` | FastAPI `/health` |
| B05 | `b05-api-check` | Проверка API без UI |
| B06 | `b06-git-branch` | Git: ветка и README |
| B07 | `b07-notes-api` | Notes API GET/POST |
| B08 | `b08-react-list` | React: список |
| B09 | `b09-react-form` | React: форма |
| B10 | `b10-docker` | Docker: образ API |
| B11 | `b11-compose` | Compose |
| B12 | `b12-sklejka` | Склейка и чеклист |

Генерация / обновление seed:

```powershell
python core/scripts/generate_learn_season_b.py
```

Чтобы залить в БД на стенде (осторожно: `reset-to-seed` затирает правки Learn): админка Learn → «Сбросить к seed» или API `POST /learn/admin/reset-to-seed`.

Или точечно создать/обновить посты через админку без полного сброса.
