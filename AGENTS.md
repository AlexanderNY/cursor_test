# AGENTS.md

Instructions for coding agents working in this repository.

## Project

**CopyParse** is a cross-posting / SMM platform: collect, process, and publish content to Telegram, VK, Instagram, Threads, Twitter/X, WordPress, Yandex Dzen, and Custom URL.

Human docs (Russian) live under `docs/` and `README.md`. Prefer those over this file for product detail.

| Doc | Use it for |
|-----|------------|
| `README.md` | Overview, quick start |
| `docs/ARCHITECTURE.md` | Graphs, ports, deploy units |
| `docs/INSTALLATION.md` | Local Docker runbook |
| `docs/SERVICES_OVERVIEW.md` | Gateway routes, UI → API |
| `docs/POSTS_LIFECYCLE.md` | `posts` / `*_posts` statuses |
| `docs/SECURITY_HARDENING.md` | Secrets, bind addresses, auth |
| `config.md` | Env vars per service |
| `deploy/DEPLOYMENT.md` | Production (ui-edge, copyparse, 9to18) |

## Layout

Python 3.12 FastAPI microservices + React/Vite UIs. Each backend service is a top-level directory with `main.py`, `config.py`, `database.py` (if it talks to Postgres), `models.py`, `routers/`, `services/`, `Dockerfile`, `requirements.txt`.

| Path | Role | Port |
|------|------|------|
| `api-gateway/` | JWT, CORS, rate limit, proxy. Only public API | 8000 |
| `auth/` | Users, tokens, groups, billing | 8001 |
| `core/` | Profiles, posts, SMM, admin, site/learn | 8002 |
| `scheduler/` | Poll schedules, wake bots | 8003 |
| `collector/` | RSS Дзен, метрики очереди | 8009 |
| `processor/` | Text / AI processing | 8010 |
| `tg-bot/` `vk-bot/` `wp-bot/` `url-bot/` | Platform collect/publish | 8004–8007 |
| `instagram-bot/` `dzen-bot/` `th-bot/` `tw-bot/` | Platform collect/publish | 8011–8014 |
| `tg-game/` | Telegram mini-game / orders | 8015 |
| `selectcb/` | Callback helper | — |
| `shared/` | Cross-service Python (`ai_client`, `retry`, `db` schemas, billing) | — |
| `shared_storage/` | Shared storage helpers copied into images | — |
| `ui-app/` | CopyParse SPA (React 18, Vite, Tailwind, TanStack Query) | 8100 |
| `deploy/ui-9to18/` | 9to18.ru SPA source | 8200 |
| `deploy/ui-edge/` | Public nginx :80/:443 | 80/443 |
| `deploy/e2e-tester/` | On-demand browser E2E (SQLite) | 8300 |
| `k8s/` | Minikube manifests (`Makefile` targets) | — |

There is **no root `package.json` or `pyproject.toml`**. Install and test inside the service you change.

`ui-9to18/` at the repo root is a leftover tree (includes `node_modules`). Canonical 9to18 app is `deploy/ui-9to18/`.

PostgreSQL 16 is **external** (not a compose service). Databases: `db_bot` (CopyParse) and `db_9to18` (site). MinIO, Redis, and Ollama **are** in `docker-compose.yaml`.

## Commands

### Backend unit tests

Pytest configs exist in `tg-bot/pytest.ini` and `tg-game/pytest.ini`. Other packages use the same layout (`tests/`). Use `python3 -m pytest` (`pytest` is often not on `PATH`).

Install that service’s `requirements.txt` plus `pytest` / `pytest-asyncio` before running. Do not rewrite pins unless the task asks.

```bash
# Shared helpers (run from repo root)
PYTHONPATH=. python3 -m pytest shared/tests -q

# Per-service: install that folder’s requirements, then pytest with repo root on PYTHONPATH
python3 -m pip install -r core/requirements.txt pytest pytest-asyncio
cd core && PYTHONPATH=..:. python3 -m pytest tests -q
```

Same pattern for `tg-bot`, `tg-game`, `url-bot`, `wp-bot`.

Regenerate greenfield SQL from schema modules (do not hand-edit the generated file as source of truth):

```bash
PYTHONPATH=. python3 -m shared.db.bootstrap
```

### UI (CopyParse)

```bash
cd ui-app
npm install
npm run lint
npm run build          # tsc -b && vite build
npm run dev            # Vite :8100, proxies /api → gateway:8000
```

### UI (9to18)

```bash
cd deploy/ui-9to18
npm install
npm run lint
npm run build          # copies pyodide, then tsc -b && vite build
```

### Full stack (only when you need running services)

Requires Docker Compose, an external PostgreSQL reachable as `host.docker.internal`, a filled `.env` from `.env.example`, and the external network `edge_net`:

```bash
cp .env.example .env                   # fill secrets; never commit
./deploy/scripts/create-edge-net.sh    # or: docker network create edge_net
docker compose up -d --build
curl -sf http://127.0.0.1:8000/health
```

UI: `http://127.0.0.1:8100`. Gateway: `http://127.0.0.1:8000`. Sequential start (lower RAM peak): `python deploy/scripts/compose_up_sequential.py`.

Do not `docker compose up` the entire stack for a unit-testable change. Selenium bots, Ollama, and MinIO are heavy.

K8s: `k8s/README.md` and root `Makefile` (`build-images`, `apply-all`). Copy `k8s/base/secret.yaml.example` → `secret.yaml` (gitignored).

## Architecture rules

- Browser → `ui-app` (`/api/...`) → **gateway** (strips `/api`) → service. Vite proxy target is `http://gateway:8000` (Docker DNS). Internal services have **no CORS**.
- Gateway validates JWT, strips client `X-User-*`, then sets `X-User-Id` / `X-User-Role` from the token. Downstream must trust only those headers from the gateway, never from the client. Do not publish auth/core ports off localhost.
- Identity spoofing: never skip JWT on a new public route unless it is an explicit allowlisted path (login, register, refresh, verify, reset-password, health, some RSS/game).
- Post pipeline: inbound → `posts` → processor → `post_targets` → bots publish. Queue is Postgres statuses + `FOR UPDATE SKIP LOCKED`, not Kafka. Details: `docs/POSTS_LIFECYCLE.md`.
- Replica-safe publishers claim rows (`publishing`). Scheduler uses `pg_try_advisory_lock`.
- `shared/` is copied into images as `/app/shared`. Import as `from shared...`. Keep it free of a single service’s business logic.
- Each service has its own `config.py` (`pydantic-settings`). Secrets default to empty strings; they come from env / `.env` / K8s Secret.

## Code conventions

### Python / FastAPI

- Python ≥ 3.12, FastAPI, Pydantic v2, `aiopg` + `psycopg2` for Postgres, `httpx` for outbound HTTP, `uvicorn`.
- `async def` for I/O; `def` for pure functions. Type-hint all signatures. Prefer Pydantic models over raw dicts (RORO).
- Files: `snake_case`. Functions: verb + `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE`.
- Guard clauses and early returns; happy path last. Expected API errors: `HTTPException`.
- Routers are declarative FastAPI routers; business logic lives in `services/`.
- Lifespan context managers for DB pools, not deprecated `@app.on_event`.
- Naming in `coderules.md`: no single-letter names except loop indices; do not shadow builtins (`list`, `dict`, `str`).

### ui-app (web, not React Native)

`.cursor/rules/ui-app-rule.mdc` talks about React Native; **this UI is a web SPA**. Use React 18 function components, TypeScript, Tailwind, React Router, TanStack Query, Axios `apiClient` in `ui-app/src/services/api-client.ts`.

- Directories: `kebab-case`. Named exports. `@/` → `ui-app/src`.
- Pages under `ui-app/src/pages/`, API wrappers under `ui-app/src/services/`, types under `ui-app/src/types/`.
- Routes: `ui-app/src/App.tsx`. Auth in `AuthProvider`. Do not add `console.log` of tokens (the client currently logs token presence; do not add more secrets logging).
- After UI changes, run `npm run lint` and `npm run build` in `ui-app`. On current `main` both commands already fail with pre-existing ESLint/tsc errors (unused vars, empty interfaces, type mismatches in platform pages). Do not “fix the whole UI” unless that is the task; check that your files did not add new errors. Exercise the changed route in the browser when a server is up; keep client state consistent across pages that share it.

### Scope

- Change the smallest set of services that implement the request. Do not “fix” unrelated bots, SQL dumps (`backub*.sql`), or leftover `ui-9to18/` at repo root.
- Do not commit `.env`, `.env.9to18`, `k8s/base/secret.yaml`, `*.pem` / `*.key`, or live credentials. Compose interpolates `$` in `.env` — JWT must be hex, not bcrypt.
- Do not deploy, publish, or mutate production (copyparse.ru / 9to18.ru) from an agent session.

## Testing

- If you touch code that already has tests, run those tests. Add tests when you add non-trivial logic next to an existing `tests/` package.
- Prefer fast unit tests. Integration against Postgres/MinIO/Telegram/VK needs secrets and running infra — skip unless the task requires it and credentials exist.
- ui-app has no Jest/Vitest suite; verification is `lint` + `tsc`/build, plus browser flow when UI behavior changed.
- Browser E2E is `deploy/e2e-tester/` (separate compose, SQLite). Not part of default PR checks (there is no GitHub Actions workflow in this repo).

## Cursor Cloud specific instructions

Cloud Agent VMs do not ship the production Postgres, Telegram/VK tokens, GPU Ollama weights, or `edge_net`. Treat the **full Compose stack as optional**.

**Default verification (no Docker, no `.env`):**

1. Python: `python3 -m pip install -r <service>/requirements.txt pytest pytest-asyncio`, then `PYTHONPATH=. python3 -m pytest shared/tests -q` and `PYTHONPATH=..:. python3 -m pytest tests -q` in the service you edited.
2. ui-app: `npm install && npm run lint && npm run build` from `ui-app/`. Expect existing failures on `main`; report only new ones on files you touched.
3. 9to18: same npm commands from `deploy/ui-9to18/` when that app changed.

**When you must run services:** confirm Docker, `edge_net`, and a usable `DATABASE_URL` first. Bind host ports stay on `127.0.0.1` except the public edge. Do not start Ollama or Chromium bots unless the change depends on them.

**UI without Compose:** `npm run dev` in `ui-app` listens on `0.0.0.0:8100`, but `/api` proxies to hostname `gateway`. Point the Vite proxy at `http://127.0.0.1:8000` only for a local-gateway session; do not commit that change unless the task is specifically local-dev DX.

**Secrets:** use `.env.example` as the name list. If a test truly needs `DATABASE_URL`, `JWT_SECRET_KEY`, or bot tokens and they are absent, stop and report the blocker instead of inventing credentials or hitting production APIs.

**Do not** use production URLs (`www.copyparse.ru`, live MinIO, real BotFather tokens) as the default test target.
