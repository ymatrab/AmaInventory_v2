# BUILD_PLAN.md — Inventory Platform

> **For Claude Code.** Read `CLAUDE.md` and `docs/` first. Then execute the phases **in order**.
> After each phase: run its **Verify** step, ensure **Acceptance** is met, then **commit**. Do not skip ahead.
> If a phase's acceptance cannot be met, **stop and report** — do not fake output or weaken the Golden Rules in `CLAUDE.md §2`.

---

## Decisions locked (do not re-litigate)

- Two apps: `gestion/` (Django+DRF+React, local/VPN) and `public-app/` (Next.js, internet).
- **Gestion runs entirely in Docker** (dev **and** prod): web, postgres, redis, celery worker, celery beat, and frontend are all containers in `gestion/docker-compose.yml`. Every gestion `make` target executes **inside** those containers (`docker compose run --rm web ...`); the host only needs Docker + Docker Compose. (See `CLAUDE.md §3`/`§5`.)
- **Outbound-only** from gestion; **no stock** on public. (See `CLAUDE.md §2`.)
- Field login = **identity link + PIN**, time-boxed to the campaign window. (SMS OTP is a documented alternative, not the default.)
- Tolerance margin = **monetary value**, set/adjustable **by CDG per warehouse** at reconciliation.
- SAP read + CSV-to-SAP = **mocked seams**; real wiring later.

## Seams to leave open (mock now, wire later)

- `gestion/backend/apps/sap/` — `SapClient` interface + `MockSapClient` (seeded system stock). `# SEAM`.
- CSV export — configurable column mapping with a documented default; `# SEAM` for the real SAP import schema.
- Field login delivery (SMS/WhatsApp) — generate + display link/PIN in gestion; actual sending is a `# SEAM`.

---

## Phase 0 — Repo, tooling, scaffolding

**Goal:** a runnable monorepo skeleton with both apps and the `make`/script targets.

Tasks:
1. Create the repo layout from `CLAUDE.md §4`. Init git, add `.gitignore`, `.editorconfig`, root `README.md`.
2. Scaffold `gestion/backend` (Django + DRF), `gestion/frontend` (Vite + React + TS), `public-app` (Next.js + TS, App Router).
3. Add `packages/tokens/` with placeholder design tokens; wire both frontends to consume them.
4. Add root task runner (`Makefile` or `package.json` scripts): `setup, db, migrate, seed, dev, test, lint, e2e`. **Gestion targets must wrap `docker compose`** (e.g. `make migrate` → `docker compose run --rm web python manage.py migrate`); do not invoke host Python/pip directly.
5. Add `.env.example` for both apps (see Appendix C). **Gestion is Docker-first:** add `gestion/backend/Dockerfile` and `gestion/docker-compose.yml` with services **web, frontend, postgres, redis, celery (worker), beat** — usable for **dev** (with code-mounted volumes + autoreload) and as the base for **prod** (Phase 10). Bind published ports to `127.0.0.1` in dev.
6. Configure linters/formatters: `ruff`+`black` (py, run inside the gestion container), `eslint`+`prettier`+`tsc --strict` (ts).

**Verify:** `make setup && make dev` starts all services (gestion stack via `docker compose up`); each app serves a placeholder page; `make lint` passes. `docker compose ps` shows web/postgres/redis/celery/beat healthy.
**Acceptance:** both apps boot; **gestion runs fully in Docker with no host-level Python/Postgres**; no secrets in repo; tokens package imported by both frontends.
**Commit:** `chore(phase-0): scaffold monorepo and tooling`.

---

## Phase 1 — Gestion backend: domain models + admin + auth

**Goal:** the system of record (local DB) with admin and role groups.

Tasks:
1. Implement the **gestion data model** (Appendix A.1) as Django apps/models with migrations.
2. Register all models in **Django admin** (campaigns, warehouses, items, assignments, field users, etc.).
3. Create auth **groups**: `Inventory Responsible`, `Audit`, `CDG`. Add a `make seed` that creates one demo user per group + demo WHS/items.
4. Add DRF base setup: auth (session), permissions per group, pagination, error format.
5. Add an **AuditLog** model + a helper/mixin that records state-changing actions.

**Verify:** `make migrate && make seed`; log into Django admin; the three groups and demo data exist.
**Acceptance:** models match Appendix A.1; group-based permissions enforced on a sample protected endpoint.
**Commit:** `feat(phase-1): gestion domain models, admin, roles`.

---

## Phase 2 — SAP seam (read-only) + system stock

**Goal:** system stock available to gestion via a mockable interface.

Tasks:
1. Define `SapClient` interface in `apps/sap/` with `get_system_stock(campaign, warehouse) -> list[SystemStockRow]`.
2. Implement `MockSapClient` returning seeded quantities/values per (warehouse, item). Toggle via `USE_SAP_MOCK`.
3. On campaign arming, **snapshot** system stock into the local `SystemStock` table (so reconciliation is stable).
4. `# SEAM` + README note describing how to implement the real connector (DB read or SAP API), read-only.

**Verify:** unit test: arming a campaign populates `SystemStock` from the mock.
**Acceptance:** no SAP code anywhere outside `apps/sap/`; mock is the default.
**Commit:** `feat(phase-2): SAP read-only seam with mock + system-stock snapshot`.

---

## Phase 3 — Public app: data model + field API skeleton

**Goal:** the public DB and field-facing endpoints (no stock).

Tasks:
1. Implement the **public data model** (Appendix A.2) with Prisma/Drizzle migrations. **No quantity/value columns.**
2. Build field API routes (Appendix B.2): `me`, `items`, `counts`, `counts/mine`, `recount`. Validate inputs with `zod`.
3. Add **window enforcement** middleware: field routes work only when the campaign is `OPEN`/`RECOUNT` and `now ∈ [open_at, close_at]`; else `403/423`.
4. Stub UI pages: landing/closed, login, my-campaign, count-entry, re-count, progress (functional, token-styled, `// DESIGN-SLOT`).

**Verify:** with a seeded `OPEN` campaign, field routes return data; with `CLOSED`, they reject.
**Acceptance:** public schema contains **no** stock/value fields; window enforcement covered by tests.
**Commit:** `feat(phase-3): public data model + field API + window enforcement`.

---

## Phase 4 — Sync layer (the one channel)

**Goal:** gestion pushes config and pulls counts; public exposes the sync API. M2M-authenticated, idempotent.

Tasks:
1. Implement public **sync endpoints** (Appendix B.1), protected by **service token + HMAC + timestamp** (reject replays).
2. Implement gestion **outbound sync client** (`apps/sync/`): `push_campaign`, `push_warehouses`, `push_items`, `push_agents`, `push_recount`.
3. Implement gestion **pull poller** (Celery beat task) `pull_counts(campaign)` using a **cursor** (`since=updated_at`); **upsert** by `line_uid`+`version`; add a manual "Sync now" action.
4. Enforce: gestion is the only initiator; public never calls gestion. Add a test asserting no inbound gestion endpoint exists for the public app.
5. Map pulled lines into gestion `Count`/`CountLine`; mark `synced_at`.

**Verify:** integration test (public running locally): push a campaign+items+agents → submit a count on public → poller pulls it into gestion idempotently (re-run = no dupes).
**Acceptance:** Appendix B contract implemented exactly; HMAC + token enforced; pull is idempotent.
**Commit:** `feat(phase-4): outbound push + idempotent pull sync with M2M auth`.

---

## Phase 5 — Public field experience: login + counting

**Goal:** an agent can log in and count during the window; counts attributed to them.

Tasks:
1. Implement **login**: `POST /api/auth/login {token, pin}` → validates token+PIN(hash)+window → scoped session (agent+campaign). Rate-limit + lockout after N PIN failures.
2. Magic link route `/c/{campaignCode}/a/{token}` pre-fills identity, then prompts PIN.
3. Build **count entry**: list item reference for the assigned WHS; enter qty **by unit / by pack**; add item not in list; save/submit; show progress. Each line gets a stable `line_uid`, `version++` on edit.
4. Build **re-count** view: shows only `flagged` items; resubmission bumps `version`.
5. Closed/expired states show the landing page; expired tokens are rejected.

**Verify:** e2e (public only): open link → enter PIN → submit counts → re-count flagged items; attempts outside window rejected.
**Acceptance:** every count line carries the agent id; window + token expiry enforced; KPIs derivable.
**Commit:** `feat(phase-5): per-agent link+PIN login and count/re-count UI`.

---

## Phase 6 — Reconciliation, margins, re-count, CSV export (gestion)

**Goal:** CDG reconciles pulled counts vs SAP-mock, sets value margins, triggers re-counts, exports CSV.

Tasks:
1. Build **reconciliation** logic: join pulled counts with `SystemStock` by `item+warehouse`; compute `gap_qty`, `gap_value` (using item value from SAP snapshot).
2. **Value margin per WHS**: CDG sets/edits a monetary margin; lines/WHS flagged `within_margin` accordingly.
3. **Flag for re-count**: CDG marks items; create a **re-count Count = copy of original** with `flagged` items; `push_recount` to public.
4. **CSV export**: configurable mapping (Appendix on format), default schema documented; `# SEAM` for real SAP import columns.
5. Lifecycle controls: Audit/CDG **open/close/extend**; closing pushes status and **expires agent tokens**.

**Verify:** unit tests for gap + margin logic; integration: flag re-count → public shows flagged items → resubmit → re-pull → CSV generated.
**Acceptance:** margin is monetary + per-WHS + CDG-editable; re-count preserves original; CSV produced.
**Commit:** `feat(phase-6): reconciliation, value margins, re-count, CSV export`.

---

## Phase 7 — Gestion frontend (React SPA)

**Goal:** the internal UI for all gestion pages (functional, token-styled).

Tasks (pages per `docs/inventory_platform_architecture.md §10.1`):
1. Auth + role-aware nav (Inv. Resp / Audit / CDG).
2. Campaigns overview; **create campaign** (scope, type, trigger, window).
3. **Assignment** (Inv. Resp) + **confirm** (Audit) + **open/close/extend** (Audit/CDG).
4. **Live counts monitoring** (per WHS/agent, from pulled data) with progress.
5. **Reconciliation workspace** (CDG): table of gaps, **set value margin per WHS**, flag re-count.
6. **Re-count management**, **CSV export** download, **sign-off tracking** (attach scanned signed sheet, mark received).
7. **Agent KPI** view; **history/archive**; placeholder **analysis dashboard**.
8. All pages use `packages/tokens` + `// DESIGN-SLOT` seams for the user's components.

**Verify:** click-through of each page against the running backend; role permissions hide/disable actions correctly.
**Acceptance:** every page in §10.1 exists and is wired to the API; no hardcoded styling.
**Commit:** `feat(phase-7): gestion react SPA pages`.

---

## Phase 8 — Security hardening

**Goal:** lock it down to the architecture's security model.

Tasks:
1. Public: Cloudflare-ready headers, rate limits (login + sync), strict CORS (field UI origin only; sync via token), input validation everywhere.
2. M2M: token rotation support (two valid keys), HMAC + timestamp replay window, optional egress-IP allow-list config.
3. Gestion: VPN/private-only binding documented; CSRF for session endpoints; audit log coverage check.
4. Verify the **outbound-only** invariant with a test/lint check; confirm public schema has no stock fields (automated assertion).
5. Secrets review: only `.env.example` in repo; document required prod secrets.

**Verify:** security test suite passes; dependency audit clean.
**Acceptance:** Golden Rules (`CLAUDE.md §2`) enforced and tested.
**Commit:** `feat(phase-8): security hardening and invariants`.

---

## Phase 9 — Tests, seed data, end-to-end

**Goal:** confidence + the full happy-path e2e.

Tasks:
1. Fill unit/integration coverage for core logic (sync idempotency, margins, window, login).
2. Rich `make seed`: a demo campaign across 2 WHS, items with variants, 2 agents, SAP-mock stock with intentional gaps.
3. Implement `make e2e` covering the Definition of Done path in `CLAUDE.md §8`.

**Verify:** `make test` and `make e2e` green from a clean checkout.
**Acceptance:** e2e passes deterministically.
**Commit:** `test(phase-9): seed data and end-to-end happy path`.

---

## Phase 10 — Deployment readiness

**Goal:** documented, repeatable deploy (Appendix D).

Tasks:
1. **Public → Vercel + Neon + Cloudflare**: build config, env, prod migrations, WAF/rate-limit notes.
2. **Gestion → local server**: `docker-compose` for web (gunicorn) + postgres + redis + celery + beat; build & serve the React SPA; VPN-only binding.
3. Write **Appendix D runbook** (env, migrate, deploy, rotate keys, smoke test) and a `docs/RUNBOOK.md`.
4. Final pass against Definition of Done.

**Verify:** follow the runbook against staging-like settings (mock SAP); smoke test the e2e path.
**Acceptance:** Definition of Done fully met.
**Commit:** `chore(phase-10): deployment configs and runbook`.

---

# Appendix A — Data Model

### A.1 Gestion DB (PostgreSQL via Django) — system of record

- **User / Group** (Django) + `FieldUserProfile`(matricule) — groups: Inventory Responsible, Audit, CDG.
- **Warehouse**: `whs_code`(unique), `name`, `city`, `active`.
- **Item**: `item_code`, `sku`, `description`, `color_parfum`, `base_unit`, `units_per_pack`, `active`. *(reference only — no quantities)*
- **FieldUser**: `matricule`(unique), `full_name`, `role`(AGENT|WAREHOUSEMAN), `phone?`.
- **Campaign**: `code`, `type`(MONTHLY|PERIOD), `trigger`(ROUTINE|HIGH_GAP|ANOMALY), `scope`(ALL|SPECIFIC), `status`(DRAFT|ARMED|OPEN|RECOUNT|CLOSED|ARCHIVED), `open_at`, `close_at`, `created_by`, `confirmed_by`, `created_at`.
- **CampaignWarehouse**: `campaign`, `warehouse`.
- **Assignment**: `campaign`, `warehouse`, `field_user`, `confirmed`(bool), `confirmed_by`, `confirmed_at`.
- **AgentCredential**: `field_user`, `campaign`, `token`(random, unique), `pin_hash`, `active`, `expires_at`. *(pushed to public)*
- **SystemStock**: `campaign`, `warehouse`, `item`, `system_qty`, `unit_value`. *(local only; from SAP mock)*
- **Count**: `campaign`, `warehouse`, `is_recount`(bool), `parent_count?`, `status`(OPEN|SUBMITTED), `synced_at`.
- **CountLine**: `count`, `item`, `qty_units`, `qty_packs`, `total_units`(computed), `counted_by`(field_user), `flagged_for_recount`(bool), `line_uid`(UUID), `version`(int), `updated_at`. *(pulled copy)*
- **Reconciliation**: `campaign`, `warehouse`, `value_margin`(decimal), `set_by`, `set_at`, `status`.
- **ReconciliationLine**: `reconciliation`, `item`, `physical_qty`, `system_qty`, `gap_qty`, `physical_value`, `system_value`, `gap_value`, `within_margin`(bool).
- **SignOff**: `campaign`, `warehouse`, `agent_signed`(bool), `warehouseman_signed`(bool), `document`(file ref), `received`(bool), `received_at`.
- **CsvExport**: `campaign`, `warehouse`, `generated_at`, `file_ref`.
- **AuditLog**: `actor`, `action`, `entity`, `entity_id`, `timestamp`, `meta`(json).

### A.2 Public DB (PostgreSQL) — NO stock, NO values

- **Campaign**: `id`(UUID = gestion id), `code`, `status`, `open_at`, `close_at`.
- **Warehouse**: `id`, `whs_code`, `name`, `city`, `campaign_id`.
- **ItemRef**: `id`, `item_code`, `sku`, `description`, `color_parfum`, `base_unit`, `units_per_pack`, `campaign_id`(or warehouse-scoped). *(no quantities)*
- **Agent**: `id`(matricule), `full_name`, `role`.
- **AgentCredential**: `agent_id`, `campaign_id`, `token`(unique), `pin_hash`, `expires_at`, `active`, `failed_attempts`.
- **CountLine**: `line_uid`(UUID, PK), `campaign_id`, `warehouse_id`, `item_code`, `qty_units`, `qty_packs`, `agent_id`, `is_recount`(bool), `flagged`(bool), `version`(int), `updated_at`, `created_at`.

> The **only** quantity data on public is what agents physically counted. No system qty, value, gap, or margin — ever.

---

# Appendix B — Sync API Contract

All **sync** endpoints (B.1) live on **public** and are called **only** by the gestion backend.
Auth headers: `Authorization: Bearer <SYNC_SERVICE_TOKEN>`, `X-Timestamp: <unix>`, `X-Signature: hmac_sha256(body, SYNC_HMAC_SECRET)`. Reject if timestamp skew > 5 min or signature invalid.

### B.1 Sync endpoints (public; gestion → public)
- `POST /api/sync/campaign` — upsert `{id, code, status, open_at, close_at}`.
- `POST /api/sync/warehouses` — upsert `[{id, whs_code, name, city, campaign_id}]`.
- `POST /api/sync/items` — upsert `[{item_code, sku, description, color_parfum, base_unit, units_per_pack, campaign_id}]`.
- `POST /api/sync/agents` — upsert `[{agent_id, full_name, role, token, pin_hash, campaign_id, expires_at}]`.
- `POST /api/sync/recount` — `{campaign_id, line_uids[] or item_codes[]}` → set `flagged=true`, create re-count context.
- `GET  /api/sync/counts?campaign={id}&since={cursor}&limit={n}` — returns `{ lines: [CountLine...], next_cursor }`, ordered by `updated_at`. Gestion upserts by `line_uid`+`version`.

### B.2 Field endpoints (public; agent session, NOT service token)
- `POST /api/auth/login` — `{token, pin}` → session (agent+campaign) if window OPEN/RECOUNT; lockout after N fails.
- `GET  /api/me` — agent + assigned warehouse(s) + campaign status.
- `GET  /api/items?warehouse={id}` — item reference for counting.
- `POST /api/counts` — `{line_uid?, item_code, qty_units, qty_packs}` → create/update line, `version++`, `updated_at=now`.
- `GET  /api/counts/mine` — agent's lines + progress.
- `GET  /api/recount` — flagged items for this agent/warehouse.

> Gestion has **no** inbound endpoint for the public app. Gestion only **consumes** B.1 (push via POST, pull via GET).

---

# Appendix C — Environment variables (`.env.example`)

**gestion/backend**
```
DJANGO_SECRET_KEY=
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://...:5432/gestion
REDIS_URL=redis://localhost:6379/0
USE_SAP_MOCK=true
SAP_DSN=                      # SEAM: real SAP read-only connection (unused while mock)
PUBLIC_API_BASE_URL=http://localhost:3000
SYNC_SERVICE_TOKEN=          # must match public
SYNC_HMAC_SECRET=            # must match public
SYNC_POLL_SECONDS=120
```

**public-app**
```
DATABASE_URL=postgres://...  # Neon/Supabase in prod
SYNC_SERVICE_TOKEN=          # must match gestion
SYNC_HMAC_SECRET=            # must match gestion
SESSION_SECRET=
LOGIN_MAX_PIN_ATTEMPTS=5
NEXT_PUBLIC_APP_NAME=Inventory
```

---

# Appendix D — Deployment Runbook (summary; expand into docs/RUNBOOK.md)

**Public (Vercel + Neon + Cloudflare)**
1. Create Neon Postgres; set `DATABASE_URL`. 2. Set sync + session secrets in Vercel env. 3. Run prod migrations. 4. Deploy Next.js to Vercel. 5. Put domain behind **Cloudflare** (WAF, rate limiting, bot protection). 6. Smoke test field login with a seeded campaign.

**Gestion (local server, VPN)**
1. `docker compose up -d` (web + postgres + redis + celery + beat). 2. `migrate` + create groups/users. 3. Set `PUBLIC_API_BASE_URL` + matching sync secrets. 4. Build React SPA; serve via nginx/Django static. 5. Bind to private interface only; confirm reachable **only over VPN**. 6. Confirm Celery beat poller is running.

**Cutover checks**: outbound-only verified · public has no stock · secrets only in env · e2e happy path green · key rotation procedure documented.

**SEAMs to wire on company network**: real `SapClient`, real CSV→SAP column mapping, login-link delivery (SMS/WhatsApp), MS SSO for gestion.
