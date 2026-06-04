# 02 · Gestion Backend (Django + DRF)

[← Documentation index](../DOCUMENTATION.md)

The internal app. Runs **entirely in Docker** on the local/VPN network. Owns SAP access,
reconciliation, margins, re-counts, CSV export, history, and is the **only** initiator of the sync
channel.

- Project root: [`gestion/backend/`](../../gestion/backend/)
- Django project package: `config/` (settings, urls, wsgi/asgi, celery)
- Apps: `apps/<name>/`
- Tests: `tests/`

---

## 1. Project configuration (`config/`)

| File | Purpose |
|------|---------|
| `config/settings.py` | All settings, env-driven. INSTALLED_APPS lists the 8 local apps. DRF uses session auth + `IsAuthenticated` by default, page size 50, and a custom error envelope (`apps.accounts.exceptions.api_exception_handler`). Defines Celery, CORS (gestion frontend origin only), the sync settings, and the SAP seam settings. |
| `config/urls.py` | URL root: `/api/health/`, Django admin at `/admin/`, and `path("api/", include("apps.accounts.urls"))`. |
| `config/celery.py` | Celery app; beat schedule `poll-open-campaigns` runs `apps.sync.tasks.poll_open_campaigns` every `SYNC_POLL_SECONDS` (default 120s). |
| `config/wsgi.py` / `asgi.py` | Server entrypoints (gunicorn in prod, runserver in dev). |

Every setting that matters is enumerated in [07 · Tooling & ops](07-tooling-and-ops.md) §env.

---

## 2. The 8 apps

All under `apps/`. Models are documented field-by-field in [01 · Data model](01-data-model.md);
this section covers **behaviour** (services, commands, admin).

### `accounts`
Identity, roles, audit.
- **Models:** `FieldUserProfile`, `FieldUser`, `AuditLog`.
- `groups.py` — constants `INVENTORY_RESPONSIBLE`, `AUDIT`, `CDG`.
- `permissions.py` — DRF permission classes `IsInventoryResponsible`, `IsAudit`, `IsCDG`.
- `audit.py` — `record_audit(actor, action, entity, entity_id, **meta)` helper used by every
  state-changing service.
- `exceptions.py` — `api_exception_handler` produces the uniform `{"error": {"code", "detail"}}`
  envelope for all DRF responses.
- `migrations/0002_role_groups.py` — **data migration** that creates the three role groups.
- `management/commands/seed_demo.py` — idempotent demo seed (see §3).
- `urls.py` / `views.py` — currently the API root include point (gestion REST viewsets land here in
  Phase 6–7).

### `warehouses`
`Warehouse` model + admin. Joined to SAP by `whs_code`.

### `items`
`Item` model + admin. Reference only.

### `campaigns`
Campaign lifecycle and credentials.
- **Models:** `Campaign`, `CampaignWarehouse`, `Assignment`, `AgentCredential`.
- **`services.py`:**
  - `arm_campaign(campaign)` — moves a campaign to `ARMED` and triggers the SystemStock snapshot
    (`apps/sap/services.py::snapshot_system_stock`), audited.
  - `hash_pin(pin)` — bcrypt hash (Python `bcrypt`, `$2b$` — verifiable by Node `bcryptjs`).
  - `generate_credentials(campaign)` — for each assigned `FieldUser`, mints a random `token` + a
    random 4-digit `PIN`, stores only the bcrypt **hash**, upserts one `AgentCredential` per agent
    (rotates token+PIN on repeat — still one row per agent), audited. Returns the plaintext
    token+PIN **once** (for handout), never persisted in clear.
  - **Lifecycle (Phase 6):** `open_campaign()` (→ `OPEN`, stamps `open_at`), `extend_campaign(new_close_at)`
    (moves the window), `close_campaign()` (→ `CLOSED`, stamps `close_at`, **deactivates + expires every
    agent credential**). Each pushes the new status outbound via `SyncClient.push_campaign` (`_push_status`),
    audited. Pushing `CLOSED` is what blocks field login (the public window check fails).
- **`management/commands/generate_credentials.py`** — `python manage.py generate_credentials <id>`
  prints `matricule  PIN=####  link=/c/{code}/a/{token}` per agent. Print-and-hand-out workflow;
  actual SMS/WhatsApp delivery is a seam.

### `counts`
The local copy of pulled counts.
- **Models:** `Count`, `CountLine` (with the `total_units` recompute-on-save logic).

### `reconciliation`
- **Models:** `SystemStock`, `Reconciliation`, `ReconciliationLine`, `SignOff`, `CsvExport`.
- **`services.py` (Phase 6):**
  - `build_reconciliation(campaign, warehouse)` — joins the SAP `SystemStock` snapshot with the
    aggregated physical counts (`_physical_by_item`, which prefers a re-counted value over the
    superseded original, BR-08) and upserts one `ReconciliationLine` per item with `gap_qty`,
    `physical_value`, `system_value`, `gap_value`. Idempotent.
  - `set_value_margin(campaign, warehouse, margin)` — sets/edits the **monetary, per-warehouse**
    margin (BR-06) and re-flags every line `within_margin` when `|gap_value| ≤ margin` (`_apply_margin`).
  - `flag_for_recount(campaign, warehouse, item_codes)` — creates a re-count `Count` as a copy of the
    preserved original (`parent_count`), flags the original lines, moves the campaign to `RECOUNT`, and
    pushes status + item codes outbound (`push_campaign` + `push_recount`).
  - `generate_csv_export(campaign, warehouse=None)` — renders the reconciliation CSV (BR-09) to
    `MEDIA_ROOT/exports/` and records a `CsvExport`. Column mapping lives in `csv_export.py`
    (`DEFAULT_COLUMNS`) with a **`# SEAM`** for the real SAP import layout — see
    [06 · SAP connector](06-sap-connector.md) §6.
- **`management/commands/reconcile.py`** — `python manage.py reconcile <id> [--margin N] [--csv]`
  builds gaps for every warehouse, optionally sets a margin and exports the CSV (CDG runner until the
  SPA lands in Phase 7).

### `sap`
The SAP read-only **seam**. Fully covered in [06 · SAP connector](06-sap-connector.md).
- `client.py` — `SapClient` ABC + `SystemStockRow` dataclass.
- `mock.py` — `MockSapClient` (default, deterministic).
- `real.py` — `RealSapClient` skeleton (inert until `_connect()` is filled).
- `queries/system_stock.sql` — placeholder SELECT.
- `services.py` — `snapshot_system_stock(campaign)`.
- `__init__.py` — `get_sap_client()` factory, toggled by `USE_SAP_MOCK`.
- `README.md` — the 3-step go-live checklist.

### `sync`
The outbound channel. Fully covered in [05 · Sync connector](05-sync-connector.md).
- `client.py` — `SyncClient` (push + pull, HMAC-signed).
- `services.py` — `push_campaign_setup()`, `pull_counts()`, `upsert_count_line()`.
- `tasks.py` — Celery tasks `poll_open_campaigns` (beat) + `pull_counts_task` (on-demand).
- `models.py` — `SyncCursor`.
- `management/commands/sync_now.py` — `python manage.py sync_now <campaign_id> [--pull-only]`.

---

## 3. Demo data — `make seed`

`apps/accounts/management/commands/seed_demo.py` is **idempotent** and loads:
- the three role groups,
- three staff users `inv_resp` / `audit` / `cdg` (password `demo12345`),
- two warehouses, three item variants,
- two field users (an agent + a warehouseman).

SAP system stock for the demo comes from the **mock** at arming time (deterministic per
warehouse/item), so reconciliation has realistic gaps to find.

---

## 4. Admin

Every model is registered in its app's `admin.py`. `AuditLog` is registered **read-only** (no add
/ change / delete) since it is append-only. Django admin at `http://127.0.0.1:8000/admin/`.

---

## 5. DRF conventions (CLAUDE.md §7)

- Thin views; business logic lives in `services.py` per app.
- Type hints throughout; `ruff` + `black` enforced (`make lint`).
- Uniform error envelope `{"error": {"code", "detail"}}` via the custom exception handler.
- Session auth + group permissions; MS SSO is a later swap-in.
- Every state-changing action calls `record_audit(...)`.

---

## 6. REST API for the SPA (Phase 7)

The SPA talks to a DRF API mounted at `/api/` (router aggregated in `apps/accounts/urls.py`):
session auth (`/api/auth/csrf|login|logout|me/`) + viewsets across `campaigns`, `assignments`,
`warehouses`, `items`, `field-users`, `counts` (monitor + KPI actions), `reconciliations`
(build/set_margin/flag_recount), `exports` (generate + download), `signoffs`, and `audit`. Views are
thin — lifecycle/reconciliation actions call the services above. Full endpoint list:
[04 · API reference](04-api-reference.md) §1. Serializers live in each app's `serializers.py`.

## 7. Frontend (React + Vite SPA) — Phase 7

- Root: [`gestion/frontend/`](../../gestion/frontend/) — Vite + React + TypeScript (strict), React Router.
- Runs in the `frontend` Docker container on **port 5174**; a Vite **proxy** forwards `/api`,
  `/admin`, `/static` to the `web` service so the SPA is same-origin (clean session cookie + CSRF).
- `src/lib/api.ts` — typed API client (adds `X-CSRFToken` on unsafe calls); `src/lib/auth.tsx` —
  auth context. Data logic is kept out of components (CLAUDE.md §6).
- Pages (architecture §10.1): **Login**, **Campaigns overview**, **Create campaign**, **Campaign
  detail** with role-aware tabs — *Lifecycle* (arm / credentials / push / open·close·extend / sync),
  *Assignment* (assign + Audit confirm), *Live counts* (per-WHS monitor), *Reconciliation* (gap
  table, set margin, flag re-count, CSV generate + download), *Sign-off*, *Agent KPI* — plus
  **History/Archive** (audit log) and a placeholder **Analysis** dashboard.
- UI primitives in `components/ui.tsx` + `components/Shell.tsx` are token-styled with
  `// DESIGN-SLOT` markers so the user's design system drops in. Role gating hides/disables actions
  by group. Builds, lints, and type-checks clean in the container.

---

## 7. Tests

`tests/` (pytest + pytest-django, run via `docker compose run --rm web pytest`):
- `test_health.py` — health endpoint.
- `test_phase1.py` — domain models, role groups, audit.
- `test_phase2.py` — SAP seam: factory returns the right client; mock determinism; real client
  raises `NotImplementedError` until wired.
- `test_phase4.py` — sync: idempotent upsert, cursor pagination, push payloads.
- `test_phase5.py` — credential generation: PIN hash verifies, rotation, no-assignment case.
- `test_phase6.py` — reconciliation: gap computation, monetary per-WHS margin + re-flagging,
  re-count preserves the original + pushes, CSV export file/record, close expires tokens, open/extend.
- `test_phase7.py` — REST API: `me` role flags, campaign CRUD + arm, reconciliation build + CSV
  download, unauthenticated rejection.

**Total: 37 gestion tests** (+ 18 public) passing.
</content>
