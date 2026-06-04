# 01 · Data Model & Database Tables

[← Documentation index](../DOCUMENTATION.md)

There are **two separate databases**. They share concepts (campaign, warehouse, item, agent,
count line) but are physically isolated and intentionally **asymmetric**: the public DB is missing
every stock/value column on purpose.

- **Gestion DB** — PostgreSQL, managed by **Django ORM** (migrations in each app's `migrations/`).
- **Public DB** — PostgreSQL, managed by **Prisma** (`public-app/prisma/schema.prisma`).

Column names below are the **database** names. Django models use snake_case attributes that match
the column; Prisma uses camelCase fields mapped to snake_case columns via `@map(...)`.

---

## 1. Gestion database (local zone — holds everything, including stock)

Source files: `gestion/backend/apps/*/models.py`.

### 1.1 `accounts` app

**`FieldUserProfile`** — extra profile data for a gestion staff (Django auth) user.

| Column | Type | Notes |
|--------|------|-------|
| `user_id` | FK → `auth_user` (OneToOne) | the Django login |
| `matricule` | varchar(50), unique | staff identifier |

**`FieldUser`** — a field worker who counts on the public app. **Not** a Django auth user;
authenticated per-campaign by link+PIN. Identified by `matricule` for KPI attribution.

| Column | Type | Notes |
|--------|------|-------|
| `matricule` | varchar(50), unique | stable identity; used as the public `Agent.id` |
| `full_name` | varchar(200) | |
| `role` | varchar(20) | `AGENT` \| `WAREHOUSEMAN` |
| `phone` | varchar(40) | for sending the link/PIN (delivery is a seam) |
| `active` | bool | |
| `created_at` | datetime | |

**`AuditLog`** — append-only record of every state-changing action on the gestion side
(CLAUDE.md §7). Written via `apps/accounts/audit.py::record_audit()`.

| Column | Type | Notes |
|--------|------|-------|
| `actor_id` | FK → `auth_user`, nullable | who did it |
| `action` | varchar(100) | e.g. `campaign.arm`, `credentials.generate` |
| `entity` | varchar(100) | model name |
| `entity_id` | varchar(64) | target row id |
| `timestamp` | datetime | indexed `-timestamp` |
| `meta` | JSON | extra context |

> **Role groups** (not a table of their own) — three Django `auth.Group`s created by data migration
> `accounts/migrations/0002_role_groups.py`: **Inventory Responsible**, **Audit**, **CDG**.
> Constants in `apps/accounts/groups.py`; enforced by `apps/accounts/permissions.py`.

### 1.2 `warehouses` app

**`Warehouse`**

| Column | Type | Notes |
|--------|------|-------|
| `whs_code` | varchar(30), unique | the SAP warehouse code (join key to SAP) |
| `name` | varchar(200) | |
| `city` | varchar(120) | |
| `active` | bool | |

### 1.3 `items` app

**`Item`** — item master / reference. **Reference only — never holds quantities** (even on the
gestion side, quantities live on count lines / system stock, not here).

| Column | Type | Notes |
|--------|------|-------|
| `item_code` | varchar(60) | part of the unique key |
| `sku` | varchar(60) | variant level; unique with `item_code` |
| `description` | varchar(300) | |
| `color_parfum` | varchar(120) | variant attribute (color / fragrance) |
| `base_unit` | varchar(20) | default `unit` |
| `units_per_pack` | uint | unit↔pack conversion during counting |
| `active` | bool | |
| — | unique | `(item_code, sku)` → `uniq_item_code_sku` |

### 1.4 `campaigns` app

**`Campaign`** — the unit of work.

| Column | Type | Notes |
|--------|------|-------|
| `code` | varchar(40), unique | human campaign id |
| `type` | varchar(10) | `MONTHLY` \| `PERIOD` |
| `trigger` | varchar(10) | `ROUTINE` \| `HIGH_GAP` \| `ANOMALY` |
| `scope` | varchar(10) | `ALL` \| `SPECIFIC` |
| `status` | varchar(10) | `DRAFT`→`ARMED`→`OPEN`→`RECOUNT`→`CLOSED`→`ARCHIVED` |
| `open_at` / `close_at` | datetime, nullable | the counting window |
| `created_by` / `confirmed_by` | FK → `auth_user`, nullable | creator + Audit confirmer |
| `created_at` | datetime | |
| `warehouses` | M2M via `CampaignWarehouse` | scope |

**`CampaignWarehouse`** — join scoping a campaign to a warehouse. Unique `(campaign, warehouse)`.

**`Assignment`** — a field user assigned to count a warehouse for a campaign. Counting can't start
until Audit confirms (BR-02). Unique `(campaign, warehouse, field_user)`.

| Column | Type | Notes |
|--------|------|-------|
| `campaign_id` / `warehouse_id` / `field_user_id` | FK | `field_user` is `PROTECT` |
| `confirmed` | bool | Audit gate |
| `confirmed_by_id` | FK → `auth_user`, nullable | |
| `confirmed_at` | datetime, nullable | |

**`AgentCredential`** — per-agent, per-campaign login, **pushed to the public app**. Only the PIN
**hash** is stored. Unique `(field_user, campaign)`.

| Column | Type | Notes |
|--------|------|-------|
| `field_user_id` / `campaign_id` | FK | |
| `token` | varchar(64), unique | goes in the magic link |
| `pin_hash` | varchar(255) | bcrypt; interoperable with Node `bcryptjs` |
| `active` | bool | revocable |
| `expires_at` | datetime, nullable | time-box |
| `created_at` | datetime | |

### 1.5 `counts` app (the local copy of pulled counts)

**`Count`** — a count of a warehouse for a campaign. A re-count is a **copy** of an original (BR-08):
`is_recount=True` with `parent_count` pointing at the preserved original.

| Column | Type | Notes |
|--------|------|-------|
| `campaign_id` / `warehouse_id` | FK | |
| `is_recount` | bool | |
| `parent_count_id` | self-FK, nullable | original preserved |
| `status` | varchar(10) | `OPEN` \| `SUBMITTED` |
| `synced_at` | datetime, nullable | last successful pull |
| `created_at` | datetime | |

**`CountLine`** — a single counted item line, pulled from the public app. **Idempotent sync key:
`line_uid` + `version`.**

| Column | Type | Notes |
|--------|------|-------|
| `count_id` | FK → `Count` | |
| `item_id` | FK → `Item` (`PROTECT`) | |
| `qty_units` | decimal(14,3) | counted loose units |
| `qty_packs` | decimal(14,3) | counted packs |
| `total_units` | decimal(16,3) | **derived** = `qty_units + qty_packs * item.units_per_pack`, recomputed on every save |
| `counted_by_id` | FK → `FieldUser`, nullable | KPI attribution |
| `flagged_for_recount` | bool | |
| `line_uid` | UUID, unique | stable across edits + sync |
| `version` | int | bumped on edit; pull skips if not newer |
| `updated_at` | datetime (`auto_now`) | |
| — | index | `(line_uid, version)` |

### 1.6 `reconciliation` app (Phase 6 consumes these; tables already exist)

**`SystemStock`** — **LOCAL ONLY** snapshot of SAP stock at arming. Never leaves the zone. Unique
`(campaign, warehouse, item)`.

| Column | Type | Notes |
|--------|------|-------|
| `campaign_id` / `warehouse_id` / `item_id` | FK | |
| `system_qty` | decimal(16,3) | theoretical quantity from SAP |
| `unit_value` | decimal(14,4) | unit cost/value from SAP |

**`Reconciliation`** — CDG reconciliation of a warehouse; `value_margin` is monetary and set per
warehouse (BR-06). Unique `(campaign, warehouse)`. `status` `OPEN`\|`COMPLETED`.

**`ReconciliationLine`** — per-item gap line: `physical_qty`, `system_qty`, `gap_qty`,
`physical_value`, `system_value`, `gap_value`, `within_margin`.

**`SignOff`** — paper sign-off tracking (legal, BR-10): `agent_signed`, `warehouseman_signed`,
`document` (file), `received`, `received_at`. Unique `(campaign, warehouse)`.

**`CsvExport`** — a generated CSV for separate SAP import (BR-09): `generated_at`, `file_ref`,
optional `warehouse`.

### 1.7 `sync` app

**`SyncCursor`** — the pull bookmark per campaign.

| Column | Type | Notes |
|--------|------|-------|
| `campaign_id` | FK | |
| `cursor` | text | compound `iso8601|line_uid`; empty means "from the start" |
| `updated_at` | datetime | |

---

## 2. Public database (internet zone — counts only, NO stock)

Source: `public-app/prisma/schema.prisma`. Migrations: `public-app/prisma/migrations/`.
Field names shown as `dbColumn` (the `@map` target).

**`campaign`** — mirror of the gestion campaign. `id` (text, mirrors gestion id), `code` (unique),
`status` (enum, default `ARMED`), `open_at`, `close_at`. **The public side only receives status;
it never advances it.**

**`warehouse`** — `id` (uuid), `whs_code`, `name`, `city`, `campaign_id`. Unique
`(campaign_id, whs_code)`.

**`item_ref`** — item reference, **no quantities**: `id`, `item_code`, `sku`, `description`,
`color_parfum`, `base_unit`, `units_per_pack`, `campaign_id`. Unique `(campaign_id, item_code, sku)`.

**`agent`** — `id` (the matricule), `full_name`, `role` (enum `AGENT`\|`WAREHOUSEMAN`).

**`agent_credential`** — `id`, `agent_id`, `campaign_id`, `token` (unique), `pin_hash`,
`expires_at`, `active`, `failed_attempts` (lockout counter). Unique `(agent_id, campaign_id)`.

**`count_line`** — what an agent physically counted. **This is the only quantity data in the public
zone.**

| Column | Type | Notes |
|--------|------|-------|
| `line_uid` | text, PK | the UUID; stable across edits/sync |
| `campaign_id` / `warehouse_id` | FK | |
| `item_code` / `sku` | text | reconciliation keys on `item_code + sku` |
| `qty_units` / `qty_packs` | decimal | what was counted |
| `agent_id` | FK → `agent` | attribution |
| `is_recount` | bool | |
| `flagged` | bool | set when gestion pushes a re-count |
| `version` | int | bumped on edit |
| `created_at` / `updated_at` | datetime | |
| — | indexes | `(campaign_id, updated_at)` for pull cursor; `(campaign_id, agent_id)` for "my counts" |

---

## 3. What the public DB deliberately does NOT have (Golden Rule §2)

This asymmetry is the whole security model. The public `count_line` and `item_ref` have **no**:

- `system_qty` / theoretical quantity
- `unit_value` / cost / price
- `total_units` derived against system data
- `gap_qty` / `gap_value`
- `value_margin`
- anything sourced from SAP

`total_units`, `SystemStock`, `Reconciliation*`, and margins exist **only** in the gestion DB
(§1.5–1.6). An automated test asserting the public schema has no stock columns is planned for
Phase 8 ([09 · Status](09-status-and-roadmap.md)).

---

## 4. How the two models line up across the boundary

| Concept | Gestion (Django) | Public (Prisma) | Joined on |
|---------|------------------|-----------------|-----------|
| Campaign | `Campaign.pk` | `campaign.id` (text) | gestion pk pushed as id |
| Warehouse | `Warehouse.pk` | `warehouse.id` | gestion pk pushed as id |
| Item | `Item(item_code, sku)` | `item_ref(item_code, sku)` | code + sku |
| Agent | `FieldUser.matricule` | `agent.id` | matricule |
| Count line | `CountLine.line_uid` + `version` | `count_line.line_uid` + `version` | UUID + version (idempotent) |

The mapping is implemented in `apps/sync/services.py::upsert_count_line()` (pull) and
`apps/sync/client.py` (push). See [05 · Sync connector](05-sync-connector.md).
</content>
