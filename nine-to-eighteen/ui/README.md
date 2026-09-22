# ui-9to18

Автономный фронтенд для **9to18.ru** (Vite + React, Bowl и Code на Pyodide).
Не входит в основной `ui-app` и backend API CopyParse.

За edge-прокси `ui-edge` слушает порт **8200** внутри сети `edge_net`.

## Маршруты

| URL | Страница |
|-----|----------|
| `/` | Главная — сетка **живых** разделов |
| `/login`, `/register` | Site auth |
| `/account` | Кабинет (прогресс Learn через site JWT) |
| `/admin`, `/admin/apps/:slug` | Супер-админ / админ сервиса |
| `/app/:slug`, `/app/:slug/:postSlug` | Страница и блог сервиса |
| `/game/bowl` | Bowl 2D — игра на Pyodide |
| `/game/code` | Code — песочница Python (Pyodide) |
| `/game/learn` | Learn — оглавление |
| `/game/learn/:slug` | Статья + лаба (запуск python в браузере) + шпаргалка |
| `/game/learn/admin…` | Learn CMS (JWT CopyParse admin/author) |
| `/game/learning-map` | Карта обучения → Learn |
| `/game/map` | Редирект на `/game/learning-map` |
| `/game/tasks` | Чек-лист прогресса |
| `/game/quiz` | Квиз из `structured.quiz` статей |
| `/game/cert` | Сертификаты сезона (печать / PDF) |

Learn: `GET /api/learn/posts` (публично), админка `/api/learn/admin/*` + `/api/auth/*`.  
Site: `/api/site/*` (аккаунты, плитки, прогресс ученика, study).  
Seed: `core/data/learn_seed.json` (B + S01 + MAP + PY + QA). Bowl/Code: Pyodide в браузере.

Прогресс ученика — только **`/site/learn/progress`** (site JWT в `db_9to18`). CopyParse JWT нужен авторам Learn CMS.

## Локальная разработка

```powershell
cd deploy/ui-9to18
npm install
# нужен gateway на :8000 (или VITE_API_GATEWAY_URL)
npm run dev
```

http://localhost:8200 — Vite проксирует `/api` → gateway.

Pyodide WASM копируется в `public/pyodide/` при `npm run dev` / `npm run build`.

## Docker (production static)

Требуется сеть `edge_net` (см. [deploy/DEPLOYMENT.md](../DEPLOYMENT.md)):

```powershell
..\scripts\create-edge-net.ps1
docker compose -f deploy/ui-9to18/docker-compose.yml up -d --build
```

Локально: http://127.0.0.1:8200 (порт привязан только к localhost).

## Вынос в отдельный репозиторий

Каталог `deploy/ui-9to18/` самодостаточен как фронт; API Learn/Site остаются в `core` монорепо.

Маршрутизация домена и TLS — в [`deploy/ui-edge`](../ui-edge/).
