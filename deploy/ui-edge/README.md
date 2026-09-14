# Edge proxy (ui-edge)

Отдельный деплой-юнит: единая точка входа HTTP/HTTPS для нескольких сайтов.

См. также [deploy/DEPLOYMENT.md](../DEPLOYMENT.md).

## Схема

```
                         ┌─ www.copyparse.ru ──→ ui:8100
                         │                         └─ /tg/game/media/ → gateway:8000
Интернет :80 / :443 ──── ui-edge (nginx)
                         │
                         └─ www.9to18.ru ──────→ ui-9to18:8200
                                                   └─ /api/learn|site|auth → gateway:8000
```

## Структура

```
deploy/ui-edge/
├── docker-compose.yml       # standalone stack (сеть edge_net)
├── README.md
├── conf.d/
│   ├── 00-upstreams.conf
│   ├── 05-default.conf
│   ├── copyparse.conf
│   └── 9to18.conf
├── includes/
│   ├── proxy-ui.conf
│   └── proxy-api-gateway.conf
├── certs/
│   ├── copyparse/
│   └── 9to18/
└── scripts/
    ├── gen-self-signed.ps1
    └── gen-self-signed.sh
```

Upstream’ы резолвятся по именам контейнеров/сервисов в сети **`edge_net`**: `ui`, `ui-9to18`, `gateway` (Docker DNS `127.0.0.11` в рантайме — edge может стартовать до приложений).

## Запуск

```powershell
# один раз
..\scripts\create-edge-net.ps1

# сертификаты (prod PEM или self-signed для проверки)
.\scripts\gen-self-signed.ps1

docker compose -f deploy/ui-edge/docker-compose.yml up -d
```

Из каталога `deploy/ui-edge`:

```powershell
docker compose up -d
docker compose exec ui-edge nginx -t
```

## 9to18.ru

HTTP и HTTPS. Сертификаты: `certs/9to18/fullchain.pem`, `privkey.pem`.

Приложение: отдельный стек [`deploy/ui-9to18/`](../ui-9to18/).

API на этом host: только `/api/learn/*`, `/api/site/*` и `/api/auth/*` → gateway (без SMM/ботов CopyParse).

## copyparse.ru

HTTP и HTTPS. Сертификаты: `certs/copyparse/`. Upstream: сервис `ui` из монорепо-compose.

## Проверка

```powershell
curl -I -H "Host: www.copyparse.ru" http://127.0.0.1
curl -I -H "Host: www.9to18.ru" http://127.0.0.1
curl -Ik -H "Host: www.9to18.ru" https://127.0.0.1
```
