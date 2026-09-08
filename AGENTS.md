# AGENTS.md

## Cursor Cloud specific instructions

This is a FastAPI microservices monorepo (Russian-language social-media multi-posting
platform) plus a React + Vite + TypeScript frontend (`ui-app`). Per-service config lives in
`<service>/config.py`; the service map is documented in `docs/SERVICES_OVERVIEW.md`.

### Core developer flow (runs fully locally, no external credentials)

`ui-app` (8100) → `api-gateway` (8000) → `auth` (8001) / `core` (8002), backed by
**PostgreSQL** (`db_bot`) and **MinIO** (S3). The bots (`tg-bot`, `vk-bot`, `wp-bot`,
`instagram-bot`, `tw-bot`, `dzen-bot`, `th-bot`, `url-bot`) require real third-party
accounts/credentials and are NOT part of the local hello-world flow. `scheduler`,
`collector`, `processor`, `selectcb` are pure-local (Postgres only) but optional.

### Infrastructure already provisioned in the VM snapshot (do NOT reinstall)

- PostgreSQL 16 is installed. Database `db_bot` exists; user `postgres` password is `1qaz!QAZ`
  (matches the `DATABASE_URL` defaults in the `config.py` files). Tables are auto-created by
  each service on startup (`init_db`), so no manual migrations are needed for the core flow.
- MinIO binary at `/usr/local/bin/minio`; data dir `/workspace/minio_data` (bucket `uploads`).
- Python deps live in `/workspace/.venv`; `ui-app/node_modules` is installed (npm).
- `/etc/hosts` maps `gateway` → `127.0.0.1`. This is REQUIRED because `ui-app/vite.config.ts`
  proxies `/api` to `http://gateway:8000`. Do not remove it (and do not edit vite.config.ts).

### Starting infrastructure (services do NOT auto-start after a fresh boot)

```bash
sudo pg_ctlcluster 16 main start            # PostgreSQL on 5432
# MinIO on 9000 (api) / 9001 (console), user admin / password123:
MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=password123 \
  /usr/local/bin/minio server /workspace/minio_data --address ":9000" --console-address ":9001"
```

### Running the core-flow services (dev mode, from repo root, using `.venv`)

Each FastAPI service is run with uvicorn `--reload` from its own directory. The non-default
env vars below are needed for local (non-Docker) runs because the committed `config.py`
defaults point at Docker IPs (`172.20.10.x`) / `host.docker.internal`:

```bash
DB='dbname=db_bot user=postgres password=1qaz!QAZ host=127.0.0.1'
V=/workspace/.venv/bin

# auth :8001
(cd auth && DATABASE_URL="$DB" $V/uvicorn main:app --reload --host 0.0.0.0 --port 8001)

# core :8002  (S3 optional: leave S3_ACCESS_KEY/S3_SECRET_KEY empty to fall back to local disk)
(cd core && DATABASE_URL="$DB" API_GATEWAY_URL=http://localhost:8000 \
  S3_ENDPOINT_URL=http://127.0.0.1:9000 S3_BUCKET=uploads \
  S3_ACCESS_KEY=admin S3_SECRET_KEY=password123 S3_USE_SSL=false \
  $V/uvicorn main:app --reload --host 0.0.0.0 --port 8002)

# api-gateway :8000  (override downstream URLs from Docker IPs to localhost)
(cd api-gateway && AUTH_SERVICE_URL=http://localhost:8001 CORE_SERVICE_URL=http://localhost:8002 \
  SCHEDULER_SERVICE_URL=http://localhost:8003 $V/uvicorn main:app --reload --host 0.0.0.0 --port 8000)

# ui :8100
(cd ui-app && npm run dev)
```

### Lint / test / build

- UI lint: `npm run lint --prefix ui-app`. NOTE: `main` already has pre-existing lint
  errors (`@typescript-eslint/no-explicit-any` in `core-service.ts` / `types/wordpress.ts`)
  and warnings — these are not caused by setup.
- UI build: `npm run build --prefix ui-app`.
- `tg-bot` has a pytest config (`tg-bot/pytest.ini`); most other services have no test suite.

### Gotchas

- `auth` register AND login both require `username`, `email`, and `password` in the JSON body
  (login is not email+password only).
- Public (no-JWT) gateway paths: `/auth/login`, `/auth/register`, `/auth/refresh`,
  `/auth/verify`, `/auth/reset-password*`, `/health`. All other gateway routes need a
  `Authorization: Bearer <access_token>` header; the gateway injects `X-User-Id`/`X-User-Role`
  downstream.
- `core/config.py` defaults to db `db_bot` even though `docker-compose.yaml` sets
  `DB_NAME=core_db`; for local dev everything uses `db_bot`.
- Postgres is intentionally NOT in `docker-compose.yaml`; it is expected as an external host.
