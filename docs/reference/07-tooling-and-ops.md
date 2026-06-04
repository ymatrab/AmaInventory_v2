# 07 · Tooling, Commands & Configuration

[← Documentation index](../DOCUMENTATION.md)

How to run, build, and configure the platform. **Gestion runs entirely in Docker** (dev and prod);
every gestion command wraps `docker compose`. The **public-app** runs on host Node (targets Vercel)
with a local Postgres container for dev.

---

## 1. Prerequisites

- **Docker + Docker Compose** — the only host requirement for gestion (no host Python/Postgres/Redis).
- **Node.js 20+ and npm** — for the public-app and the gestion frontend tooling.

---

## 2. Make targets (the task runner)

From the repo root. Defined in [`Makefile`](../../Makefile).

| Target | What it does |
|--------|--------------|
| `make env` | Create `gestion/.env` and `public-app/.env` from the committed `.example` templates (if missing). |
| `make setup` | `docker compose build` the gestion images, `npm install` the public-app, start the public Postgres, `prisma generate`. |
| `make db` | Start datastores only: gestion Postgres + Redis, and the public-app Postgres. |
| `make migrate` | gestion migrations (in the `web` container) **+** `prisma migrate deploy` for public. |
| `make seed` | Demo data: gestion `seed_demo` (groups/users/warehouses/items/field users) **+** public OPEN campaign seed. |
| `make dev` | Bring up the **full gestion stack** (web, frontend, postgres, redis, celery worker, celery beat) + public Postgres in the background, then run the public-app dev server in the foreground. |
| `make up` / `make down` | Start / stop both compose stacks (detached). |
| `make test` | gestion `pytest` (in container) **+** public `vitest`. |
| `make lint` | gestion backend `ruff` + `black --check` (container), gestion frontend `eslint` (container), public-app `eslint` (host). |
| `make e2e` | Full happy-path E2E — **implemented in Phase 9**. |
| `make clean` | `down -v` both stacks (wipes local DB volumes). |

### Gestion commands run inside containers
Anything touching the gestion backend is `docker compose -f gestion/docker-compose.yml run --rm web ...`:

```bash
docker compose -f gestion/docker-compose.yml run --rm web python manage.py migrate
docker compose -f gestion/docker-compose.yml run --rm web python manage.py seed_demo
docker compose -f gestion/docker-compose.yml run --rm web python manage.py generate_credentials <id>
docker compose -f gestion/docker-compose.yml run --rm web python manage.py sync_now <id> [--pull-only]
docker compose -f gestion/docker-compose.yml run --rm web pytest -q
```

---

## 3. The gestion Docker stack

[`gestion/docker-compose.yml`](../../gestion/docker-compose.yml). Six services, **all ports bound to
`127.0.0.1`** (private only — never `0.0.0.0` on a public host):

| Service | Image / build | Dev port (127.0.0.1) | Role |
|---------|---------------|----------------------|------|
| `postgres` | postgres:16-alpine | 5432 | gestion DB (volume `pgdata`) |
| `redis` | redis:7-alpine | 6379 | Celery broker/result backend |
| `web` | `./backend` | 8000 | Django + DRF (runserver dev / gunicorn prod) |
| `celery` | `./backend` | — | Celery worker (sync jobs) |
| `beat` | `./backend` | — | Celery beat (the `poll-open-campaigns` schedule) |
| `frontend` | node:20-alpine | 5174 | React (Vite) dev server |

Env is injected via the `x-backend-env` YAML anchor (DATABASE_URL, REDIS_URL, DJANGO_SECRET_KEY,
USE_SAP_MOCK, PUBLIC_API_BASE_URL, SYNC_*). Code is bind-mounted for autoreload in dev.

> Gestion services must only ever be reachable over the local/VPN network. The `127.0.0.1` bindings
> enforce this in dev; production must bind to the private interface behind the VPN (Phase 10).

### The public-app dev database
[`public-app/docker-compose.yml`](../../public-app/docker-compose.yml) — a separate Postgres on
**port 5433**, user `ama`, db `public_app` (the name `public` is a reserved Postgres role). This is
a **different trust zone** from gestion and is intentionally a separate compose file.

---

## 4. Service URLs (dev)

| App | URL |
|-----|-----|
| Gestion API (Django) | http://127.0.0.1:8000 |
| Gestion admin | http://127.0.0.1:8000/admin/ |
| Gestion frontend (Vite) | http://127.0.0.1:5174 |
| Public app (Next.js) | http://127.0.0.1:3000 |

---

## 5. Configuration / environment variables

Secrets never enter the repo — only `.env.example` files are committed (Golden Rule §3).

### Gestion — [`gestion/.env.example`](../../gestion/.env.example) → `gestion/.env`

| Variable | Default (dev) | Purpose |
|----------|---------------|---------|
| `DJANGO_SECRET_KEY` | dev-insecure-change-me | Django signing key |
| `DEBUG` | true | Django debug |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | Django allowed hosts |
| `CORS_ALLOWED_ORIGINS` | http://localhost:5174,… | gestion frontend origin(s) only |
| `POSTGRES_USER/PASSWORD/DB` | gestion | gestion Postgres container |
| `DATABASE_URL` | postgres://gestion:gestion@postgres:5432/gestion | Django DB |
| `REDIS_URL` | redis://redis:6379/0 | Celery broker/result |
| `USE_SAP_MOCK` | true | **true = mock SAP; false = real connector** |
| `SAP_DSN / DRIVER / HOST / PORT / DB / USER / PASSWORD` | empty | real SAP connection (filled on the company network) |
| `PUBLIC_API_BASE_URL` | http://host.docker.internal:3000 | where the sync client pushes/pulls |
| `SYNC_SERVICE_TOKEN` | empty | **must match public** |
| `SYNC_HMAC_SECRET` | empty | **must match public** |
| `SYNC_POLL_SECONDS` | 120 | beat poll interval |
| `VITE_API_BASE_URL` | http://localhost:8000 | frontend → backend |

### Public-app — [`public-app/.env.example`](../../public-app/.env.example) → `public-app/.env`

| Variable | Default (dev) | Purpose |
|----------|---------------|---------|
| `DATABASE_URL` | postgresql://ama:ama@localhost:5433/public_app | public Postgres (Neon/Supabase in prod) |
| `SYNC_SERVICE_TOKEN` | empty | **must match gestion** |
| `SYNC_HMAC_SECRET` | empty | **must match gestion** |
| `SESSION_SECRET` | empty | signs the `ama_session` field cookie |
| `LOGIN_MAX_PIN_ATTEMPTS` | 5 | PIN lockout threshold |
| `NEXT_PUBLIC_APP_NAME` | Inventory | branding |

> The two `SYNC_*` secrets are **shared** and must be identical on both sides for the channel to
> authenticate (see [05 · Sync connector](05-sync-connector.md) §1).

---

## 6. Shared design tokens — `packages/tokens/`

CSS variables (colors, spacing, etc.) consumed by **both** frontends as the `@ama/tokens` workspace
package. Components reference tokens, never hardcoded values (CLAUDE.md §6), so the user's own
design system can drop in. Files: `tokens.css`, `index.js`, `index.d.ts`, `package.json`.

---

## 7. Quick start

```bash
make setup     # build images, install deps, prisma generate
make migrate   # gestion + prisma migrations
make seed      # demo data on both sides
make dev       # full gestion stack + public dev server
# gestion admin: inv_resp / audit / cdg  (password demo12345)
# public login:  open http://127.0.0.1:3000  token "demo-token" PIN 1234
make test && make lint
```
</content>
