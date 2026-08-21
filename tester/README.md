# E2E Tester

On-demand сервис для браузерных E2E против уже запущенного основного стека.
Своя Postgres хранит только сценарии, креды и отчёты. Chromium ходит на `ui:8100` через `edge_net`.

## Требования

1. Сеть `edge_net` существует.
2. Основной `docker compose` поднят (`ui` и `gateway` на `edge_net`).

```bash
# один раз
docker network create edge_net

# основной стек (из корня репозитория)
docker compose up -d
```

## Запуск тестера

```bash
cp tester/.env.example tester/.env
# Сгенерируйте Fernet-ключ:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Впишите в TESTER_SECRET_KEY=

docker compose -f tester/docker-compose.yml --env-file tester/.env up -d --build
# или:
docker compose -f docker-compose.tester.yml --env-file tester/.env up -d --build
```

Панель: [http://127.0.0.1:8300](http://127.0.0.1:8300)

В основном UI (роль admin): страница **/e2e-tester** с этой же инструкцией.

Остановка:

```bash
docker compose -f tester/docker-compose.yml --env-file tester/.env down
```

Тома `tester_pg_data` / `tester_artifacts` сохраняются до `down -v`.

## Использование

1. **Credentials** — логин/пароль пользователя продукта или JWT (`access_token` / `refresh_token`). Секреты шифруются Fernet и не отдаются в API-списках.
2. **Scenarios** — YAML/JSON шаги или `.py` Playwright-скрипт. Примеры: `tester/examples/`.
3. **Runs** — Start → live-логи → скриншоты при ошибках.

### Готовые наборы (каталог UI E2E)

| Файл | ID | Креды | Покрытие |
|------|-----|-------|----------|
| `suite_smoke.yaml` | S00, S01, S02, S10–S12, S20, S27 | admin | login, nav, Checks health, Brands/Channels/Posts, Telegram, Custom URL |
| `suite_platforms.yaml` | S20–S27 | любой пользователь | TG, VK, IG, Threads, WP, Dzen, Twitter, Custom URL |
| `suite_checks.yaml` | S02, S30–S37 | admin | Administration, Polls, Collector/Processor/Scheduler/AI, posting diag, docs |

Также: `login_smoke.yaml` / `login_smoke.py` — минимальный логин.

JWT: перед сценарием токены кладутся в `localStorage` (`access_token` / `refresh_token`), как в `ui-app`.

Password: удобный шаг `login_form` или ручные `fill` / `click`.

## YAML actions

| action | поля |
|--------|------|
| `goto` | `path` или `url` |
| `fill` | `selector`, `value` или `value_from` (`credentials.username` / `password` / `access_token` / `refresh_token`) |
| `click` | `selector` |
| `wait` | `ms` |
| `wait_url` | `contains`, опционально `timeout_ms` |
| `assert_text` | `selector`, `contains` |
| `assert_url` | `contains` |
| `screenshot` | `name` |
| `login_form` | использует password-креды и форму `/sign-in` |

## Playwright `.py`

Скрипт должен объявить:

```python
async def run(page, base_url, credentials, log):
    ...
```

Запрещены импорты `os`, `subprocess`, `socket`, `httpx` и т.п., а также `eval` / `exec` / `open`.

## Важно

- Тесты мутируют данные staging/prod-like окружения. Используйте отдельные учётки и cleanup-шаги.
- Порт панели только на `127.0.0.1:8300`.
- Health: `GET /api/health`.
