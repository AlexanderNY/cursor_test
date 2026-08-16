# Установка CopyParse

## Требования

- Docker Engine + Docker Compose plugin
- PostgreSQL 16.x доступный с хоста/контейнеров (`host.docker.internal` или LAN IP)
- (Опционально) NVIDIA GPU + драйверы для Ollama
- Windows: PowerShell; Linux/macOS: bash

Минимум для локальной разработки: Docker, PostgreSQL, свободные порты 8000–8015, 8100, 9000–9001, 11434.

## 1. Клонирование и секреты

```powershell
cd D:\Project\cursor_test   # или ваш путь
copy .env.example .env
```

Отредактируйте `.env`:

| Переменная | Назначение |
|------------|------------|
| `DATABASE_URL` | PostgreSQL, например `dbname=db_bot user=postgres password=... host=host.docker.internal` |
| `JWT_SECRET_KEY` / `SECRET_KEY` | Одинаковые; `openssl rand -hex 32` (без `$`) |
| `GAME_BOT_TOKEN` | Токен tg-game от BotFather (обязателен; старый из git отозвать) |
| `GAME_ADMIN_API_TOKEN` | Сильный токен админ-API игры (`openssl rand -hex 32`) |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | MinIO |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | Консоль MinIO |
| `S3_PUBLIC_ENDPOINT_URL` | URL MinIO для браузера, локально `http://localhost:9000` |
| `DB_POOL_MAXSIZE` | Пул на сервис (дефолт 8); сумма × число сервисов &lt; Postgres `max_connections` |
| `TRUSTED_PROXY_CIDRS` | CIDR для доверия `X-Forwarded-For` (дефолт loopback + `172.20.0.0/16`) |
| `SELENIUM_MAX_CONCURRENT` | Лимит параллельных Chrome (дефолт 2) |
| `AI_MAX_CONCURRENT` | Параллельные вызовы Ollama (дефолт 1) |
| `TELEGRAM_PROXY_URL` | Опционально SOCKS5 при блокировке TG |
| `TZ` | Часовой пояс расписаний, по умолчанию `Europe/Moscow` |
| `AI_ENABLED` | Жёсткий выключатель Ollama (`true`/`false`) |
| `VK_OAUTH_ALLOWED_FRONTENDS` | Доп. origins для редиректа после VK OAuth |

В `.env` для Compose символ `$` интерполируется — не используйте bcrypt-хеши как JWT; литеральный `$` пишите как `$$`.

Порты приложений (кроме UI через edge) привязаны к **127.0.0.1**. Публичный вход — только ui-edge :80/:443.

Безопасность: [SECURITY_HARDENING.md](SECURITY_HARDENING.md). При росте нагрузки рассмотрите PgBouncer перед Postgres (сумма пулов сервисов).

Подробнее о конфигах сервисов: [../config.md](../config.md).

## 2. Сеть edge_net

Один раз:

```powershell
.\deploy\scripts\create-edge-net.ps1
```

```bash
./deploy/scripts/create-edge-net.sh
# или: docker network create edge_net
```

Без этой сети `docker compose up` упадёт (`edge_net` объявлена как `external`).

## 3. Локальный запуск (монорепо)

Из корня репозитория:

```powershell
docker compose up -d --build
```

UI: http://127.0.0.1:8100  
API Gateway: http://127.0.0.1:8000  
MinIO Console: http://127.0.0.1:9001  

Проверка:

```powershell
curl http://127.0.0.1:8000/health
docker compose ps
```

### Всё вместе с edge и 9to18

```powershell
.\deploy\scripts\create-edge-net.ps1
.\deploy\ui-edge\scripts\gen-self-signed.ps1   # если нет сертификатов
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d --build
```

Тогда публичные :80/:443 обслуживает ui-edge (Host: copyparse.ru / 9to18.ru).

## 4. Production на VM

Полная инструкция: [../deploy/DEPLOYMENT.md](../deploy/DEPLOYMENT.md).

Кратко:

```powershell
.\deploy\scripts\create-edge-net.ps1
# положить TLS в deploy/ui-edge/certs/{copyparse,9to18}/
docker compose up -d --build
docker compose -f ui-9to18/docker-compose.yml up -d --build
docker compose -f deploy/ui-edge/docker-compose.yml up -d
```

DNS A-записи доменов → IP VM. Снаружи открыть только 80/443.

## 5. Kubernetes (Minikube)

См. [../k8s/README.md](../k8s/README.md):

1. `cp k8s/base/secret.yaml.example k8s/base/secret.yaml` и заполнить секреты  
2. Собрать образы в docker Minikube  
3. `kubectl apply` манифестов / `make apply-all`

## 6. Типовые проблемы

| Симптом | Что проверить |
|---------|----------------|
| `network edge_net not found` | `create-edge-net` скрипт |
| Auth/Core 500 на старте | `DATABASE_URL`, доступ к PostgreSQL с контейнера |
| Картинки не открываются в UI | `S3_PUBLIC_ENDPOINT_URL`, MinIO :9000 |
| Telegram не логинится | `TELEGRAM_PROXY_URL`, API id/hash в профиле |
| AI «Включена», но ошибки | контейнер `ollama`, `ollama-init`, `AI_ENABLED` |
| Compose «съел» секрет | `$` в `.env` — удвоить или сменить на hex JWT |

## 7. Остановка

```powershell
docker compose down
# с volumes (осторожно — сессии TG и данные MinIO в ./minio_data остаются на диске):
# docker compose down -v
```

## Связанные документы

- [ARCHITECTURE.md](ARCHITECTURE.md) — схемы  
- [SECURITY_HARDENING.md](SECURITY_HARDENING.md) — секреты, порты, auth  
- [USER_GUIDE.md](USER_GUIDE.md) — работа в UI  
- [SERVICES_OVERVIEW.md](SERVICES_OVERVIEW.md) — API и БД  
- [SSL_CERT_RENEWAL.md](SSL_CERT_RENEWAL.md) — сертификаты  
