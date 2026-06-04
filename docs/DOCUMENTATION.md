# AmaInventory — Project Documentation

> **Start here.** This is the master index for everything that has been built. It explains
> what each document covers, who it is for, and the order to read them in.

AmaInventory is a monthly **inventory-control platform** built as **two apps that behave like
one product**, separated by a hard security boundary:

| App | Lives in | Trust zone | Role |
|-----|----------|------------|------|
| **gestion** | [`gestion/`](../gestion/) | Local network / VPN | Owns SAP data, reconciliation, margins, re-counts, CSV export, history. Runs entirely in Docker. |
| **public-app** | [`public-app/`](../public-app/) | Public internet (Vercel) | Field counting app for agents. Holds **no stock data**. |

The two communicate over **one outbound-only channel**: gestion always initiates, the public
app never calls back. See [§ Golden Rules](#golden-rules) below.

---

## How to read this documentation

The docs are layered from **context → design → detail → operations**. Read top-down the first
time; afterwards jump straight to the reference you need.

### 1. Context (the "why" and "what") — *already in the repo, read these first*
| Document | What it gives you |
|----------|-------------------|
| [`CLAUDE.md`](../CLAUDE.md) | The operating manual: the Golden Rules, tech stack, repo layout, conventions, Definition of Done. **Authoritative — overrides everything else.** |
| [`docs/inventory_process.md`](inventory_process.md) | The **business process**: who does what during a monthly inventory, the business rules (BR-01…BR-10), roles. |
| [`docs/inventory_platform_architecture.md`](inventory_platform_architecture.md) | The **system design**: trust zones, components, the sync contract, page inventory. |
| [`BUILD_PLAN.md`](../BUILD_PLAN.md) | The ordered, phase-by-phase plan the code was built against (Phases 0–10). |

### 2. Reference (the "how it is actually built") — *this set, under [`docs/reference/`](reference/)*
Read these in order to understand the implementation. Each is self-contained.

| # | Document | Read it when you want to… |
|---|----------|---------------------------|
| 00 | [Architecture & trust zones](reference/00-architecture.md) | See the big picture: the two apps, the boundary, data flow end-to-end. |
| 01 | [Data model & database tables](reference/01-data-model.md) | Look up any table/column in **either** database, and see what is deliberately absent on the public side. |
| 02 | [Gestion backend (Django)](reference/02-gestion-backend.md) | Understand the 8 Django apps, their models, services, management commands, admin. |
| 03 | [Public app (Next.js)](reference/03-public-app.md) | Understand the field app: pages, components, libs, session auth. |
| 04 | [API reference](reference/04-api-reference.md) | Look up any HTTP endpoint — field API **and** sync API — with payloads and status codes. |
| 05 | [Sync connector & contract](reference/05-sync-connector.md) | Understand the outbound-only channel: push/pull, HMAC auth, idempotency, cursors. |
| 06 | [SAP connector (the seam)](reference/06-sap-connector.md) | Wire the real SAP SQL when you have credentials. **This is the go-live checklist.** |
| 07 | [Tooling, commands & configuration](reference/07-tooling-and-ops.md) | Run the stack: Docker, Makefile, ports, every environment variable. |
| 08 | [Security model](reference/08-security.md) | Verify the Golden Rules in code: trust boundaries, auth, secrets, what protects the local zone. |
| 09 | [Build status & roadmap](reference/09-status-and-roadmap.md) | See exactly what is done (Phases 0–7 + SAP prep) and what remains (Phases 8–10). |
| 10 | [Running & manually testing locally](reference/10-local-testing.md) | **Bring the whole platform up and click through it** — setup, URLs, logins, test tracks, troubleshooting. |
| 11 | [Design system (`@amafin/ui`)](reference/11-design-system.md) | The vendored component library: how it's wired into the gestion SPA, how to use it in a page, and how to update it. |

### 3. Operations
Deployment runbook lives in `BUILD_PLAN.md` Appendix D and will be expanded to `docs/RUNBOOK.md`
in Phase 10. Day-to-day commands are in [reference/07-tooling-and-ops.md](reference/07-tooling-and-ops.md).

---

## Keeping these docs up to date

**These docs are part of the deliverable, updated at the end of every phase** (CLAUDE.md §7). When a
phase finishes, before committing:

1. Update the affected reference pages (data model, API reference, backend/app, sync/SAP, security).
2. Move the phase from "remaining" to "done" in
   [reference/09-status-and-roadmap.md](reference/09-status-and-roadmap.md).
3. Keep this index and the root `README.md` build-status line accurate.

If code and docs disagree, the code is the truth and the docs are a bug — fix them in the same phase.

---

## Golden Rules

These are non-negotiable. Every document and every line of code respects them. Full text in
[`CLAUDE.md`](../CLAUDE.md) §2.

1. **Connections are outbound-only from gestion.** Gestion initiates every call to the public
   API (push config, pull counts). The public app **never** calls into the local network, and no
   inbound port to the local zone is ever opened.
2. **No stock leaves the local zone.** The public DB may hold campaigns, warehouses, item
   reference (code/name/variant/unit — **no quantities**), agent logins, and submitted counts. It
   **never** stores system quantities, costs, values, gaps, or margins.
3. **Secrets never enter the repo.** Only `.env.example` is committed; real `.env`/`.env.local`
   are gitignored.
4. **SAP and CSV-to-SAP are seams, not implementations.** They sit behind an interface with a
   working mock; the real connector is wired later on the company network.
5. **Field auth is per-agent and time-boxed.** Login = unique link + PIN, valid only during the
   campaign window, revocable, always attributed to an agent.

---

## One-paragraph summary of what exists today

The full **gestion** Django backend (8 apps, all models + migrations + admin + role groups), the
**SAP seam** (mock active, real connector scaffolded and inert), the **outbound sync channel**
(signed push + idempotent cursor-based pull, Celery-beat poller), per-agent **credential
generation**, the full **public Next.js field app** (Prisma schema with no stock columns, field API,
sync-receiving API, link+PIN login with lockout, and the counting/re-count/progress pages), and the
**reconciliation engine** (gap + monetary per-WHS margin, re-count, CSV export with a SAP seam,
campaign open/close/extend lifecycle), and the **gestion REST API + React SPA** (session auth,
campaigns/assignment/confirm/lifecycle, live-counts monitor, the CDG reconciliation workspace,
re-count, CSV download, sign-off, agent KPI, history) are all built and tested. Phases 0–7 plus SAP
preparation are complete (37 gestion + 18 public tests passing; frontend builds clean). Security
hardening, the end-to-end happy path, and deployment configs (Phases 8–10) remain. See
[reference/09-status-and-roadmap.md](reference/09-status-and-roadmap.md).
</content>
</invoke>
