# ui-9to18

Фронтенд для **9to18.ru**. За edge-прокси `ui-edge` на порту **8200** (внутри Docker-сети).

Сейчас — заглушка «Сайт в разработке». Публичный доступ по **HTTP** (без TLS).

## Локальная разработка

```powershell
cd ui-9to18
npm install
npm run dev
```

http://localhost:8200

## Docker

Поднимается вместе с `ui-edge`:

```powershell
docker compose up -d ui-9to18 ui-edge
```

Проверка: http://9to18.ru (нужна A-запись на IP сервера).

## HTTPS позже

Сертификаты в `deploy/ui-edge/certs/9to18/`, блок `listen 443 ssl` в `deploy/ui-edge/conf.d/9to18.conf`.
