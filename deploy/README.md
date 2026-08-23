# Standalone deploy units

Сервисы вне основного `docker-compose.yaml` (CopyParse / `ui-app`). Каждый юнит — свой `docker-compose.yml` и отдельный жизненный цикл.

| Каталог | Назначение | Compose | Порты |
|---------|------------|---------|-------|
| [ui-edge/](ui-edge/) | Публичный reverse-proxy nginx | `deploy/ui-edge/docker-compose.yml` | :80 / :443 |
| [ui-9to18/](ui-9to18/) | Сайт 9to18.ru (отдельный SPA) | `deploy/ui-9to18/docker-compose.yml` | :8200 (внутри `edge_net`) |
| [e2e-tester/](e2e-tester/) | On-demand E2E против основного UI | `deploy/e2e-tester/docker-compose.yml` | 127.0.0.1:8300 |

Общая Docker-сеть **`edge_net`**: `deploy/scripts/create-edge-net.ps1` (или `.sh`).

Порядок прод-деплоя и TLS: [DEPLOYMENT.md](DEPLOYMENT.md).

Основной стек (ui-app, gateway, backend): `docker compose up -d` из корня репозитория.
