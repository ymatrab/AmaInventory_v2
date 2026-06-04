# 09 · Build Status & Roadmap

[← Documentation index](../DOCUMENTATION.md)

Built phase-by-phase per [`BUILD_PLAN.md`](../../BUILD_PLAN.md). This is the honest state as of the
last commit on `main`.

---

## 1. Done — Phases 0–7 + SAP prep

| Phase | Title | Delivered |
|-------|-------|-----------|
| **0** | Scaffold & tooling | Monorepo, root `Makefile`, gestion Docker stack (6 services, `127.0.0.1`-bound), public-app + Prisma, shared `packages/tokens`, `.env.example` both sides, health endpoint. |
| **1** | Gestion domain models | All 8 Django apps with models + migrations + admin; role groups (Inventory Responsible / Audit / CDG) via data migration; `AuditLog` + `record_audit`; DRF permission classes + error envelope; `seed_demo`. |
| **2** | SAP read-only seam | `SapClient` ABC + `SystemStockRow`; `MockSapClient` (default, deterministic); `snapshot_system_stock` on arming; `get_sap_client()` factory; `USE_SAP_MOCK` toggle. |
| **SAP prep** | Real connector scaffold | `RealSapClient` wired into the factory (inert until `_connect()` filled); `queries/system_stock.sql` placeholder + SAP B1 example; `apps/sap/README.md` 3-step go-live checklist. |
| **3** | Public data model + field API | Prisma schema (no stock columns); field routes `me`/`items`/`counts`/`counts/mine`/`recount`; campaign-window enforcement (423); zod validation; error envelope. |
| **4** | Outbound sync | `SyncClient` (signed push + pull); idempotent `upsert_count_line` (key `line_uid`+`version`); compound cursor `updated_at|line_uid`; `SyncCursor`; Celery-beat poller; `sync_now` command; public `/api/sync/*` with HMAC auth. |
| **5** | Field auth + counting UI | Per-agent `generate_credentials` (token + bcrypt PIN hash, rotatable); link+PIN login with window check + lockout + signed httpOnly session; magic-link page; `LoginForm`, `CountTable`; wired pages my-campaign / count / recount / progress. |
| **6** | Reconciliation, margins, re-count, CSV | `build_reconciliation` (join counts × `SystemStock` → `gap_qty`/`gap_value`); monetary per-WHS `value_margin` (CDG-editable, re-flags `within_margin`); `flag_for_recount` (re-count copy preserves original, pushes status + item codes); `generate_csv_export` (+ `csv_export.py` mapping with SAP `# SEAM`); campaign `open`/`close`/`extend` lifecycle (close expires tokens); `reconcile` management command. |
| **7** | Gestion REST API + React SPA | DRF API (session auth + viewsets for campaigns/assignments/warehouses/items/field-users/counts/reconciliations/exports/signoffs/audit); React Router SPA (Login, Campaigns overview, Create, Campaign detail with role-aware tabs: Lifecycle, Assignment, Live counts, Reconciliation workspace, Sign-off, Agent KPI; History/Archive; Analysis placeholder); Vite proxy for same-origin session+CSRF; token-styled `// DESIGN-SLOT` UI. |

**Tests:** 37 gestion (pytest) + 18 public (vitest), all passing. Frontend builds/lints/type-checks clean.

**Commits on `main`:** scaffold → docs restructure → phase-1 → phase-2 → SAP scaffold → phase-3 →
phase-4 → phase-5 → docs → phase-6 → phase-7.

---

## 2. Remaining — Phases 8–10

### Phase 8 — Security hardening *(next up)*
Cloudflare-ready headers, rate limits (login + sync), strict CORS, service-token rotation, HMAC
replay window review, VPN-only binding docs, full audit-log coverage, **automated assertion that
the public schema has no stock columns**, secrets review. (See [08 · Security](08-security.md) §8.)

### Phase 9 — Rich seed + end-to-end
Fill coverage gaps; rich seed (2 WHS, item variants, 2 agents, SAP-mock gaps); `make e2e` runs the
full Definition-of-Done happy path: create → confirm → push → login → count → pull → reconcile +
margin → flag re-count → push re-count → re-submit → CSV export → close (tokens expire).

### Phase 10 — Deployment readiness
Public → Vercel + Neon + Cloudflare (build/env/migrations/WAF). Gestion → local server prod
`docker compose` (gunicorn, built SPA, VPN-only binding). `docs/RUNBOOK.md`. Final Definition-of-Done
pass.

---

## 3. External inputs needed before going fully live

These are deliberate seams — the platform is built around them and runs today on mocks/defaults:

| Input | Where it plugs in | Doc |
|-------|-------------------|-----|
| **SAP SQL + credentials** | `apps/sap/queries/system_stock.sql`, `RealSapClient._connect()`, `SAP_*` env, `USE_SAP_MOCK=false` | [06 · SAP connector](06-sap-connector.md) §4 |
| **CSV → SAP column mapping** | `reconciliation` CSV export (`# SEAM`) | Phase 6 |
| **Magic link / PIN delivery** (SMS/WhatsApp) | `generate_credentials` prints them today; sending is a seam | [02 · Gestion backend](02-gestion-backend.md) §2 `campaigns` |
| **Shared sync secrets + session secret** | `SYNC_SERVICE_TOKEN`, `SYNC_HMAC_SECRET`, `SESSION_SECRET` env on both sides | [07 · Tooling](07-tooling-and-ops.md) §5 |
| **Custom design system** | `// DESIGN-SLOT` components + `packages/tokens` | CLAUDE.md §6 |

---

## 4. Definition of Done (whole project)

From CLAUDE.md §8 — the platform is "ready to deploy" when `make dev` runs both apps, `make test` +
`make lint` pass, `make e2e` passes the full happy path, the public app enforces the window and
stores no stock, SAP + CSV are isolated seams with mocks, `.env.example` is complete with no secrets
committed, and the deploy runbook is followed. **Items 1, parts of 3–5 are met today; the `make e2e`
path (item 2) and the runbook (item 6) complete in Phases 9–10.**
</content>
