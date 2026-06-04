# CLAUDE.md — Inventory Platform

> This file is auto-loaded by Claude Code. It is the **operating manual** for this repo.
> Detailed, ordered build steps live in **`BUILD_PLAN.md`** — read it before starting and follow it phase by phase.
> Business context: **`docs/inventory_process.md`**. System design: **`docs/inventory_platform_architecture.md`**.

---

## 1. What we are building

A monthly **inventory-control platform** made of **two apps that must behave like one product**:

- **`gestion/`** — internal app (Inventory Responsible, Audit, CDG). Runs on the **company local network behind a VPN**, has **read-only SAP access**, owns reconciliation, margins, re-counts, CSV export, sign-off, history.
- **`public-app/`** — internet-facing app for **field users (Inventory Agent + Warehouseman)** who do the physical count. Hosted publicly. **Has no SAP access and no stock data.**

The two communicate over **one channel** described below.

---

## 2. THE GOLDEN RULES (never violate)

1. **Connections are outbound-only from gestion.** The gestion backend **initiates every** call to the public API (push config, pull counts). The public app **never** calls into the local network. **Never** add a webhook/endpoint that the public app calls on the gestion side. **Never** open an inbound port to the local network.
2. **No stock leaves the local zone.** The public DB may hold campaigns, WHS, **item reference (code/name/variant/unit — no quantities)**, agent logins, and submitted counts. It must **never** store or receive system quantities, costs, values, gaps, margins, or anything from SAP.
3. **Secrets never enter the repo.** Use `.env` locally and `.env.example` as the template. No keys, tokens, passwords, or connection strings committed.
4. **SAP and CSV-to-SAP are seams, not implementations.** Wire them behind an interface with a working **mock** + demo data. The real connector/mapping is added later on the company network. Mark these with `# SEAM: ...`.
5. **Field auth is per-agent and time-boxed.** Login = unique identity link + PIN, valid only during the campaign window, revocable. Counts are always attributed to an agent (for KPIs).

---

## 3. Tech stack (decided)

| | gestion (local, VPN) | public-app (internet) |
|---|---|---|
| Backend | **Django + Django REST Framework** | **Next.js (App Router) API routes** |
| Frontend | **React (Vite) SPA** | **Next.js (React)** |
| DB | **PostgreSQL** | **PostgreSQL** (Neon/Supabase in prod) |
| Async | **Celery + Redis** (sync poller, jobs) | — |
| Runtime / Hosting | **Docker Compose** — dev **and** prod — on the local server, behind VPN | **Vercel** + **Cloudflare** (WAF) |
| Auth | Django auth + Groups (MS SSO later) | per-agent link + PIN session |

> The public stack may be swapped to Django+DRF+React if requested; the **sync contract** (Appendix B of BUILD_PLAN) stays identical either way.

> **Gestion runs entirely in Docker.** Every gestion service — Django **web** (gunicorn/runserver), **PostgreSQL**, **Redis**, **Celery worker**, **Celery beat**, and the **frontend** dev/build — runs as a container defined in `gestion/docker-compose.yml`, in **both development and production**. Do **not** run the gestion backend or its database directly on the host; `make dev` brings the whole gestion stack up with `docker compose up`, and every `make` target that touches gestion (`setup`, `db`, `migrate`, `seed`, `test`, `lint`) executes **inside the gestion containers** (e.g. `docker compose run --rm web ...`). Host prerequisites for gestion are limited to **Docker + Docker Compose** (no host-level Python/Postgres needed). The `public-app` (Next.js) targets **Vercel** and runs on its own Node toolchain; a local Dockerfile for it is optional.

---

## 4. Repository layout

```
inventory-platform/
├── CLAUDE.md
├── BUILD_PLAN.md
├── docs/                       # process + architecture (reference)
├── gestion/
│   ├── backend/                # Django project
│   │   ├── config/             # settings, urls, asgi/wsgi
│   │   ├── apps/
│   │   │   ├── accounts/       # users, groups, field-user identities
│   │   │   ├── warehouses/
│   │   │   ├── items/          # item master / reference
│   │   │   ├── campaigns/      # campaign + assignment + lifecycle
│   │   │   ├── counts/         # pulled counts + lines
│   │   │   ├── reconciliation/ # margins, gaps, re-count, CSV export
│   │   │   ├── sap/            # SEAM: read-only connector (+ mock)
│   │   │   └── sync/           # outbound push client + pull poller
│   │   └── tests/
│   ├── frontend/               # React (Vite) SPA
│   │   └── src/{api,pages,components,lib}
│   └── docker-compose.yml      # web + postgres + redis + celery(+beat)
├── public-app/                 # Next.js
│   ├── app/                    # pages + /api routes (field + sync)
│   ├── lib/{auth,sync,db}
│   └── db/                     # schema + migrations (Prisma or Drizzle)
└── packages/
    └── tokens/                 # shared design tokens (see §6)
```

---

## 5. Commands (keep these working and documented)

Define and maintain these so `npm run`/`make` targets exist. **All gestion commands run via Docker Compose** (`docker compose ... ` under `gestion/`); never assume host-level Python/Postgres/Redis.

- **Install:** `make setup` (builds the gestion Docker images via `docker compose build`; installs public-app deps).
- **DB up + migrate + seed:** `make db` (`docker compose up -d postgres redis`) / `make migrate` (`docker compose run --rm web python manage.py migrate`) / `make seed` (`docker compose run --rm web python manage.py seed_demo` — demo campaign, WHS, items, agents, system stock mock).
- **Run dev (all):** `make dev` — `docker compose up` for the **full gestion stack** (web, frontend, postgres, redis, celery worker, celery beat) **plus** the public-app dev server.
- **Test:** `make test` (gestion: `docker compose run --rm web pytest`; public: vitest/jest). **Lint:** `make lint` (gestion runs `ruff`/`black` inside the container).
- **E2E happy path:** `make e2e` (see Definition of Done).

> Gestion services must only be reachable over the local/VPN network — bind container ports to the **private interface** (or `127.0.0.1` in dev), never `0.0.0.0` on a public host.

If a tool isn't available, install it; if a command can't be made to work, **stop and report** rather than faking output.

---

## 6. Frontend / design — IMPORTANT

The user will **add their own React components + design system after scaffolding**. Therefore:

- Build **functional, minimally-styled** UI. Do **not** invest in custom visual design or heavy CSS.
- Centralize look-and-feel in `packages/tokens/` (CSS variables / Tailwind config) and reference tokens, never hardcoded colors/spacing.
- Keep components **small, presentational, and clearly named** so the user's components can drop in with minimal rewiring. Put a `// DESIGN-SLOT:` comment where a custom component is expected.
- Keep all data-fetching/business logic in hooks/services **separate** from presentation.

---

## 7. Working conventions

- **Work phase by phase** per `BUILD_PLAN.md`. Do not jump ahead. After each phase: run its verification, then **commit** (`feat(phase-N): ...`, conventional commits).
- **Update the docs at the end of every phase.** A phase is not done until `docs/` reflects it: update the relevant [`docs/reference/`](docs/reference/) pages (data model, APIs, backend/app, sync/SAP, etc.) and the status in [`docs/reference/09-status-and-roadmap.md`](docs/reference/09-status-and-roadmap.md). [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md) is the master index — keep it accurate. Treat docs as part of the deliverable, not an afterthought.
- **Write tests** alongside features; a phase isn't done until its acceptance criteria pass.
- **Python:** type hints, `ruff` + `black`, DRF serializers/viewsets, thin views / logic in services.
- **TS:** strict mode, `zod` for input validation on public API routes.
- **Idempotent sync:** count lines carry a stable `line_uid` (UUID) + `version`; upserts key on those. Never create duplicates on re-poll.
- **Audit log** every state-changing action on the gestion side (actor, action, entity, timestamp).
- **Never** weaken the Golden Rules (§2) to make something easier — stop and ask instead.

---

## 8. Definition of Done (whole project)

The platform is "ready to deploy" when:

1. `make dev` runs **both** apps locally; `make test` and `make lint` pass.
2. `make e2e` passes the full happy path: **create campaign → confirm (Audit) → push to public → agent logs in (link+PIN) → submits counts → gestion pulls counts → CDG reconciles vs SAP-mock & sets value margin → flag re-count → push re-count → agent re-submits → CSV export generated → campaign closed (tokens expire).**
3. Public app enforces the **campaign window** and stores **no stock**.
4. SAP + CSV mapping are isolated behind **seams** with working mocks and a documented TODO for the real wiring.
5. `.env.example` complete for both apps; **no secrets committed**.
6. `BUILD_PLAN.md` Appendix D (deploy runbook) is followed and accurate.
