# ui-9to18

Автономный фронтенд для **9to18.ru** (Vite + React, игра Bowl на Pyodide).
Не входит в основной `ui-app` и backend API CopyParse.

За edge-прокси `ui-edge` слушает порт **8200** внутри сети `edge_net`.

## Маршруты

| URL | Страница |
|-----|----------|
| `/` | Главная — сетка разделов |
| `/game/bowl` | Bowl 2D — игра на Pyodide (перки, заказы) |
| `/game/learn` | Learn — оглавление (статьи + Anki) |
| `/game/learn/admin/login` | Learn — вход (JWT CopyParse: admin/author) |
| `/game/learn/admin` | Learn — админка: список записей |
| `/game/learn/admin/new` | Learn — создать запись |
| `/game/learn/admin/:slug` | Learn — редактировать (StructuredPost + лаба) |
| `/game/learn/:slug` | Learn — статья (Anki/квиз) + опциональная лаба |
| `/game/learning-map` | Карта обучения — профили и листья → Learn |
| `/game/:slug` | Страница раздела (заглушка) |

Learn читает/пишет контент через API gateway: `GET /api/learn/posts` (публично), админка — `/api/learn/admin/*` + `/api/auth/*`. Seed: `core/data/learn_seed.json` (B + S01 + MAP). Bowl: localStorage (сейв + заказы).

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

Dev-режим (Vite):

```powershell
docker compose -f deploy/ui-9to18/docker-compose.yml -f deploy/ui-9to18/docker-compose.dev.yml up -d --build
```

Из каталога `deploy/ui-9to18`:

```powershell
docker compose up -d --build
```

## Вынос в отдельный репозиторий

Каталог `deploy/ui-9to18/` самодостаточен: скопируйте его как корень нового repo. Dockerfile уже использует context `.`.

Маршрутизация домена и TLS — в [`deploy/ui-edge`](../ui-edge/).
