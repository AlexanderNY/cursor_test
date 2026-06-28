# Edge proxy (ui-edge)

Единая точка входа HTTP/HTTPS для нескольких сайтов на одном сервере.

## Схема

```
                         ┌─ www.copyparse.ru ──→ ui:8100
                         │                         └─ /tg/game/media/ → gateway:8000
Интернет :80 / :443 ──── ui-edge (nginx)
                         │
                         └─ www.9to18.ru ──────→ ui-9to18:8200  (HTTP, без TLS)
```

## Структура каталогов

```
deploy/ui-edge/
├── README.md
├── conf.d/
│   ├── 00-upstreams.conf
│   ├── 05-default.conf
│   ├── copyparse.conf           # активен
│   └── 9to18.conf               # HTTP-only (HTTPS — позже)
├── includes/
│   ├── proxy-ui.conf
│   └── proxy-api-gateway.conf
└── certs/
    ├── copyparse/
    └── 9to18/                   # fullchain.pem + privkey.pem
```

Приложение второго сайта: **`ui-9to18/`** (Vite + React, порт 8200).

## 9to18.ru

Работает по **HTTP** (порт 80), без сертификата. Заглушка «Сайт в разработке» в `ui-9to18/`.

DNS: A-записи `9to18.ru` и `www.9to18.ru` → IP сервера.

```powershell
docker compose up -d ui-9to18 ui-edge
curl -I http://9to18.ru
```

### HTTPS (когда будет сертификат)

1. `deploy/ui-edge/certs/9to18/fullchain.pem` и `privkey.pem`
2. Добавить в `conf.d/9to18.conf` блок `listen 443 ssl`
3. `docker compose up -d ui-edge`

### Уже настроено

- `gateway` → `CORS_ORIGINS` включает `9to18.ru` / `www.9to18.ru`
- `ui-9to18/vite.config.ts` → `allowedHosts: ['.9to18.ru']`

## copyparse.ru

Работает по умолчанию при `docker compose up -d ui-edge ui`.

## Проверка конфигурации

```powershell
docker compose exec ui-edge nginx -t
```

## Связанная документация

- [docs/SSL_CERT_RENEWAL.md](../../docs/SSL_CERT_RENEWAL.md) — TLS для copyparse (аналогично для 9to18)
- [ui-9to18/README.md](../../ui-9to18/README.md) — фронтенд 9to18
