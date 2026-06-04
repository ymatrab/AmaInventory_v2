# CLAUDE.md — AmaInventory (Public Field App)

> Operating manual for the **public** side of the inventory platform.
> The internal gestion app lives in the separate **AmaFinance** repo.
> Business context: `docs/inventory_process.md`. Architecture: `docs/inventory_platform_architecture.md`.

---

## 1. What this app does

**AmaInventory** is the internet-facing field counting app used by:
- **Inventory Agent** — logs in with a unique link + PIN, submits physical counts room by room
- **Warehouseman** — assists agents in the physical count

It is hosted on **Vercel** behind **Cloudflare** (WAF). It has **no SAP access and no stock data** — it only holds campaign configuration, warehouse assignments, item references (code/name/variant/unit — no quantities), agent credentials, and submitted count lines.

It receives configuration from the AmaFinance gestion app (push) and exposes count data for AmaFinance to pull. All communication is **initiated by AmaFinance** — this app never calls into the local network.

---

## 2. THE GOLDEN RULES (never violate)

1. **Never call into the local network.** AmaFinance initiates every sync call. This app only receives pushes and answers pulls. Never add an outbound call to the company network.
2. **No stock data.** This app must never store system quantities, costs, values, gaps, margins, or any SAP data. Only item reference (code/name/variant/unit) is allowed.
3. **Secrets never enter the repo.** Use `.env` locally, `.env.example` as the template. No keys, tokens, passwords, or connection strings committed.
4. **Field auth is per-agent and time-boxed.** Login = unique link + PIN, valid only during the campaign window, revocable. Counts are always attributed to an agent.

---

## 3. Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js (App Router) |
| API routes | Next.js `/api` routes (field API + sync-receiving API) |
| Database | PostgreSQL — Neon/Supabase in prod, local Docker container in dev |
| ORM | Prisma |
| Auth | Per-agent link + PIN session (bcrypt, signed cookie) |
| Hosting | Vercel + Cloudflare WAF |

---

## 4. Repository layout

```
AmaInventory/
├── public-app/
│   ├── app/                    # Next.js pages + /api routes
│   │   ├── c/[code]/           # campaign entry (link-based login)
│   │   ├── count/              # counting interface
│   │   └── api/
│   │       ├── auth/           # login + logout
│   │       ├── counts/         # submit count lines
│   │       └── sync/           # AmaFinance push/pull endpoints
│   ├── lib/
│   │   ├── auth.ts             # PIN session logic
│   │   ├── sync.ts             # HMAC verification for sync requests
│   │   └── db.ts               # Prisma client singleton
│   ├── prisma/
│   │   └── schema.prisma       # DB schema (no stock columns)
│   └── tests/
├── packages/
│   └── tokens/                 # @ama/tokens — CSS design tokens
├── docs/
│   └── reference/
├── Makefile
└── .gitignore
```

---

## 5. Commands

| Command | What it does |
|---------|-------------|
| `make setup` | Install deps, start local Postgres, generate Prisma client |
| `make migrate` | Run Prisma migrations |
| `make seed` | Seed demo campaign data |
| `make dev` | Start the Next.js dev server at http://127.0.0.1:3000 |
| `make test` | Run vitest |
| `make lint` | eslint + tsc |
| `make clean` | Stop containers and wipe local DB |

---

## 6. Sync contract with AmaFinance

AmaFinance calls this app (outbound from their side = inbound here).

**Endpoints this app exposes for AmaFinance:**
- `POST /api/sync/campaigns/{code}/setup` — receive campaign config + warehouse + items
- `POST /api/sync/campaigns/{code}/status` — receive lifecycle status (OPEN, CLOSED, RECOUNT)
- `POST /api/sync/campaigns/{code}/recount` — receive item codes flagged for re-count
- `GET  /api/sync/campaigns/{code}/counts` — return cursor-paginated count lines

All sync requests carry a Bearer token + HMAC-SHA256 signature + X-Timestamp (5-min anti-replay). Both tokens (`SYNC_SERVICE_TOKEN`, `SYNC_HMAC_SECRET`) must match the AmaFinance `.env`.

---

## 7. Field auth flow

1. Agent receives a unique URL: `/c/{campaign_code}/a/{token}`
2. App verifies the token is valid, not expired, and the campaign is `OPEN`
3. Agent enters their 4-digit PIN; bcrypt-verified against the stored hash
4. On success: a signed session cookie is set (agent ID + campaign + expiry)
5. After 5 wrong PINs: credential locked (requires re-generation in AmaFinance)
6. On campaign `CLOSED`: all sessions invalidated, new logins blocked

---

## 8. Working conventions

- **TypeScript:** strict mode, `zod` for input validation on all API routes.
- **No stock columns:** enforce in the Prisma schema — if a column name suggests stock/cost/value/quantity, it must not exist.
- **Idempotent sync:** count lines carry a stable `line_uid` + `version`; upserts key on those.
- **Never** weaken the Golden Rules — stop and ask instead.
- After each significant change: run `make test` and `make lint`.
