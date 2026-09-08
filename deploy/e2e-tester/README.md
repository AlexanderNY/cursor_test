# E2E Tester

Локальный on-demand сервис браузерных E2E в **одном Docker-контейнере**.

- Данные: **SQLite** (`/data/tester.db`) + скриншоты в volume `tester_data`
- Отдельный Postgres **не нужен** (не использует `db_bot` / `db_9to18`)
- Панель: [http://127.0.0.1:8300](http://127.0.0.1:8300)

## Запуск

```bash
cp deploy/e2e-tester/.env.example deploy/e2e-tester/.env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# → TESTER_SECRET_KEY=...

docker compose -f deploy/e2e-tester/docker-compose.yml --env-file deploy/e2e-tester/.env up -d --build
# или из корня:
docker compose -f docker-compose.tester.yml --env-file deploy/e2e-tester/.env up -d --build
```

Остановка:

```bash
docker compose -f deploy/e2e-tester/docker-compose.yml --env-file deploy/e2e-tester/.env down
```

Данные сохраняются в volume `tester_data` до `down -v`.

### Куда ходит Chromium

| Цель | `TARGET_UI_URL` |
|------|-----------------|
| Публичный сайт | `https://www.copyparse.ru` |
| Сайт на этом ПК | `http://host.docker.internal:8100` |

`host.docker.internal` уже проброшен через `extra_hosts` в compose.

## Быстрый старт: smoke на copyparse.ru

1. Панель → **Sites**: seed `copyparse` → `https://www.copyparse.ru`.
2. **Builder** или **Scenarios → Upload** JSON.
3. **Credentials** → логин/пароль (только в UI).
4. **Runs** → Start → HTML/ZIP отчёт.

## Smoke на 9to18 (локально)

1. Поднимите ui-9to18 (порт 8200) и этот tester.
2. `TARGET_UI_URL=http://host.docker.internal:8200`
3. Upload [`examples/nine_to_eighteen_smoke.yaml`](examples/nine_to_eighteen_smoke.yaml).
4. **Runs** → Start.

Сервис **только локальный** (`127.0.0.1:8300`), без облачной панели.

## Пример: VK Create Post

[`examples/copyparse_vk_create_post.json`](examples/copyparse_vk_create_post.json) — login → home → VKontakte → Create Post `ТЕСТ` → Posts → Refresh → assert.

## Discovery

Рекурсивный обход same-origin: **Discovery** → отметить links/buttons → **В Builder** / **Создать сценарий**.

## Builder

`POST /api/scenarios/from-config` — base URL, login, pages[], buttons[].  
`POST /api/scenarios/upload` — свой JSON/YAML/.py.

## JSON schema v2

`sections` → `subsections` → `on_enter` / `actions`. Fail-soft по дереву. Flat YAML v1 совместим.

### Actions

| action | поля |
|--------|------|
| `goto` | `path` или `url` |
| `fill` | `selector`, `value` / `value_from` |
| `type` | TipTap/contenteditable; `clear` |
| `click` | `selector` |
| `wait` | `ms` |
| `wait_url` | `contains`, `timeout_ms` |
| `assert_text` | `selector`, `contains` |
| `assert_url` | `contains` |
| `screenshot` | `name` |
| `login_form` | `sites.meta.login` / `defaults.login` |

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/sites` |
| GET/POST | `/api/credentials` |
| GET/POST | `/api/scenarios`, `/upload`, `/from-config` |
| GET/POST | `/api/runs`, `…/report.html`, `…/report.zip` |
| GET/POST | `/api/discoveries`, `…/to-scenario` |
| GET | `/api/health` |

## Важно

- Не коммитьте пароли в examples / `.env`.
- Порт панели: `127.0.0.1:8300`.
- Хранилище: SQLite в `/data/tester.db` внутри volume.
