# CopyParse

Платформа кросспостинга и SMM: сбор, обработка и публикация контента в Telegram, VK, Instagram, Threads, Twitter/X, WordPress, Яндекс Дзен и Custom URL.

## Документация

| Документ | Содержание |
|----------|------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Графы архитектуры, порты, пайплайн постов |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Установка и локальный запуск |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Инструкция для пользователя UI |
| [docs/SERVICES_OVERVIEW.md](docs/SERVICES_OVERVIEW.md) | API Gateway, эндпоинты, БД |
| [docs/POSTS_LIFECYCLE.md](docs/POSTS_LIFECYCLE.md) | Статусы `posts` / `*_posts` |
| [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md) | Прод: ui-edge, copyparse, 9to18 |
| [k8s/README.md](k8s/README.md) | Kubernetes / Minikube |
| [config.md](config.md) | Переменные окружения сервисов |

## Архитектура (кратко)

```mermaid
flowchart LR
  User[Browser] --> Edge[ui-edge :80/:443]
  Edge --> UI[ui :8100]
  Edge --> GW[gateway :8000]
  GW --> Auth & Core & Scheduler
  GW --> Bots[tg/vk/wp/url/ig/dzen/th/tw]
  Core --> PG[(PostgreSQL)]
  Collector & Processor --> PG
  Bots --> PG & MinIO[(MinIO)]
```

Полные схемы: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Быстрый старт

```powershell
copy .env.example .env
# заполните DATABASE_URL, JWT_SECRET_KEY, SECRET_KEY, MinIO-пароли

.\deploy\scripts\create-edge-net.ps1
docker compose up -d --build
```

- UI: http://127.0.0.1:8100  
- Gateway: http://127.0.0.1:8000/health  

Локально с edge + 9to18:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
```

Подробно: [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Три деплой-юнита

| Юнит | Compose | Порты |
|------|---------|-------|
| copyparse (монорепо) | `docker-compose.yaml` | UI 8100, API 8000, боты, MinIO, Ollama |
| ui-9to18 | `ui-9to18/docker-compose.yml` | :8200 |
| ui-edge | `deploy/ui-edge/docker-compose.yml` | :80 / :443 |

Сеть `edge_net` создаётся скриптом `deploy/scripts/create-edge-net.ps1` (или `.sh`).

## Стек

- Python 3.12+, FastAPI, PostgreSQL 16, MinIO (S3), Ollama (AI)
- React + Vite (ui-app)
- Боты: Telethon, Selenium/Chromium где нужно, платформенные API

## Платформы

Telegram · VKontakte · Instagram · Threads · Twitter/X · WordPress · Яндекс Дзен · Custom URL
