# Независимый стек 9to18.ru

UI + FastAPI (`site-api`, `resume-api`) + БД `db_9to18`. Связь с CopyParse — только через `ui-edge` (Host/TLS).

## Состав

| Сервис | Порт | Роль |
|--------|------|------|
| `ui-9to18` | 8200 | SPA (nginx) |
| `site-api` | 8020 | `/site/*`, `/learn/*` |
| `resume-api` | 8021 | `/resume/*` (HH-резюме) |

## Быстрый старт

```powershell
# сеть для edge
..\deploy\scripts\create-edge-net.ps1   # или: docker network create edge_net

cp .env.example .env
# заполнить DATABASE_URL (dbname=db_9to18) и JWT_SECRET_KEY

docker compose up -d --build
curl http://127.0.0.1:8020/health
curl http://127.0.0.1:8021/health
curl http://127.0.0.1:8200/
```

Локальная разработка UI без Docker:

```powershell
cd ui
npm install
# site-api :8020 и resume-api :8021 (или VITE_SITE_API_URL / VITE_RESUME_API_URL)
npm run dev
```

## Миграция Learn из db_bot

Если в `db_bot` уже есть живые `learn_posts`:

```powershell
psql -U postgres -d db_9to18 -f sql/migrate_learn_from_db_bot.sql
```

Иначе при первом старте `site-api` засеет таблицу из `api/data/learn_seed.json`.

## Learn CMS

Только супер-админ сайта (`site_users.site_role = site_admin`), вход через `/login` 9to18.

## HH-резюме

- Анкета и фото: `site-api` (`/site/me/profile`, `/site/me/photo`)
- Формирование: `resume-api`
  - опросник → шаблон: `GET /resume/questionnaire`, `POST /resume/questionnaire/apply`
  - навыки Learn: `POST /resume/generate`
  - правка: `PUT /resume`, превью: `GET /resume/preview`
- UI:
  - `/game/hh-resume/quiz` — опросник
  - `/game/hh-resume/edit` — правка текста + «Обогатить навыками из Learn»
  - `/game/hh-resume` — превью / печать

## Edge

`deploy/ui-edge/conf.d/9to18.conf` проксирует `/api/(site|learn)` → `site-api:8020`, `/api/resume` → `resume-api:8021`.
