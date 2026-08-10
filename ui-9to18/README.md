# ui-9to18

Автономный фронтенд для **9to18.ru** (Vite + React, игра Bowl на Pyodide).
Без связи с `ui-app` и backend API.

За edge-прокси `ui-edge` слушает порт **8200** внутри сети `edge_net`.

## Маршруты

| URL | Страница |
|-----|----------|
| `/` | Главная — сетка разделов |
| `/game/bowl` | Bowl 2D — игра на Pyodide |
| `/game/:slug` | Страница раздела (заглушка) |

## Локальная разработка

```powershell
cd ui-9to18
npm install
npm run dev
```

http://localhost:8200

Pyodide WASM копируется в `public/pyodide/` при `npm run dev` / `npm run build`.

## Docker (production static)

Требуется сеть `edge_net` (см. [deploy/DEPLOYMENT.md](../deploy/DEPLOYMENT.md)):

```powershell
..\deploy\scripts\create-edge-net.ps1
docker compose -f ui-9to18/docker-compose.yml up -d --build
```

Dev-режим (Vite):

```powershell
docker compose -f ui-9to18/docker-compose.yml -f ui-9to18/docker-compose.dev.yml up -d --build
```

## Вынос в отдельный репозиторий

Каталог `ui-9to18/` самодостаточен: скопируйте его как корень нового repo. Dockerfile уже использует context `.`.

Маршрутизация домена и TLS остаются в [`deploy/ui-edge`](../deploy/ui-edge/).
