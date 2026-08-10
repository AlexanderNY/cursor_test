# Деплой: ui-edge, 9to18, copyparse

Три независимых деплой-юнита на одной VM с общей Docker-сетью `edge_net`.

```
Internet :80/:443
        │
        ▼
   ui-edge (nginx) ── Host copyparse.ru ──► ui:8100 (+ /tg/game/media/ → gateway:8000)
                   └── Host 9to18.ru   ──► ui-9to18:8200
```

## 1. VM и DNS

1. Поднимите VM и назначьте **публичный IP** (или NAT 80/443 на эту машину).
2. DNS A-записи на IP VM:
   - `copyparse.ru`, `www.copyparse.ru`
   - `9to18.ru`, `www.9to18.ru`
3. Firewall: снаружи только **80** и **443**. Порты приложений (8100, 8200, 8000) не публиковать в интернет.
4. Установите Docker Engine + Compose plugin.

## 2. Сеть edge_net

Один раз на хосте:

```powershell
# Windows
.\deploy\scripts\create-edge-net.ps1
```

```bash
# Linux / macOS
./deploy/scripts/create-edge-net.sh
```

Или вручную: `docker network create edge_net`.

## 3. TLS-сертификаты

Положите PEM-файлы в `deploy/ui-edge/certs/`:

| Сайт | Файлы |
|------|--------|
| copyparse | `copyparse/fullchain.pem`, `copyparse/privkey.pem` |
| 9to18 | `9to18/fullchain.pem`, `9to18/privkey.pem` |

Подробности: [docs/SSL_CERT_RENEWAL.md](../docs/SSL_CERT_RENEWAL.md).

Для локальной проверки можно сгенерировать self-signed:

```powershell
.\deploy\ui-edge\scripts\gen-self-signed.ps1
```

## 4. Порядок запуска

Из корня репозитория (или после выноса юнитов в отдельные клоны — из их каталогов):

```powershell
# 1) copyparse (монорепо): ui + gateway + backend
docker compose up -d

# 2) сайт 9to18
docker compose -f ui-9to18/docker-compose.yml up -d

# 3) edge (публичные 80/443)
docker compose -f deploy/ui-edge/docker-compose.yml up -d
```

Имена сервисов в `edge_net` должны совпадать с upstream’ами nginx: `ui`, `ui-9to18`, `gateway`.

## 5. Проверка

```powershell
curl -I -H "Host: www.copyparse.ru" http://127.0.0.1
curl -I -H "Host: www.9to18.ru" http://127.0.0.1
curl -Ik https://127.0.0.1 -H "Host: www.copyparse.ru"
curl -Ik https://127.0.0.1 -H "Host: www.9to18.ru"
```

## 6. Локальная разработка (всё вместе)

```powershell
.\deploy\scripts\create-edge-net.ps1
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
```

`docker-compose.dev.yaml` добавляет `ui-edge` и `ui-9to18` к монорепо-стеку.
