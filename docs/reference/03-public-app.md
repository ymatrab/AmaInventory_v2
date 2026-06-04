# 03 · Public App (Next.js field app)

[← Documentation index](../DOCUMENTATION.md)

The internet-facing app field users open on their phones to perform the physical count. **Holds no
SAP data, no stock, no values.** Hosted on Vercel in production; in dev it runs on host Node with a
local Postgres in Docker.

- Root: [`public-app/`](../../public-app/)
- Framework: Next.js (App Router) — pages and `/api` routes in the same project.
- DB: PostgreSQL via **Prisma** (`prisma/schema.prisma`, see [01 · Data model](01-data-model.md) §2).

---

## 1. Directory map

```
public-app/
├── app/                      # App Router: pages + API routes
│   ├── api/                  # backend routes (see 04 · API reference)
│   │   ├── auth/{login,logout}/route.ts
│   │   ├── me/route.ts
│   │   ├── items/route.ts
│   │   ├── counts/route.ts            # POST submit/update a line
│   │   ├── counts/mine/route.ts       # my lines + progress
│   │   ├── recount/route.ts           # my flagged lines
│   │   └── sync/{campaign,warehouses,items,agents,recount,counts}/route.ts
│   ├── c/[campaign]/a/[token]/page.tsx # magic-link landing (prefills token)
│   ├── login/page.tsx
│   ├── my-campaign/page.tsx
│   ├── count/page.tsx
│   ├── recount/page.tsx
│   ├── progress/page.tsx
│   └── layout.tsx, page.tsx, globals.css
├── components/
│   ├── Shell.tsx             # DESIGN-SLOT layout wrapper
│   ├── LoginForm.tsx         # token + PIN form
│   └── CountTable.tsx        # per-item live save, add-item, flagged highlight
├── lib/                      # framework-light logic (unit-testable)
├── prisma/                   # schema, migrations, seed
└── tests/                    # vitest
```

---

## 2. The `lib/` layer (where the logic lives)

Kept separate from React so it is unit-testable and framework-light.

| File | Responsibility |
|------|----------------|
| `lib/db.ts` | Prisma client singleton. |
| `lib/errors.ts` | `ApiError(status, code, detail)` — framework-free, thrown everywhere. |
| `lib/http.ts` | `errorResponse(err)` → uniform `{"error":{"code","detail"}}` envelope (mirrors gestion). |
| `lib/validation.ts` | zod `countSubmitSchema` (`warehouse_id`, `item_code`, `sku`, `qty_units`, `qty_packs`, optional `line_uid`). |
| `lib/window.ts` | `isCampaignOpen({status,openAt,closeAt})` and `assertCampaignOpen()` (throws `ApiError(423)`). Enforces the counting window. |
| `lib/pin.ts` | `verifyPin(pin, pinHash)` via `bcryptjs` (interoperable with Python `bcrypt`). |
| `lib/session-crypto.ts` | `signSession()` / `verifySession()` — `base64url(payload).base64url(HMAC-SHA256)`, timing-safe compare. |
| `lib/session.ts` | `getSession()` / `requireSession()` reading the signed httpOnly cookie `ama_session` (maxAge 12h). |
| `lib/campaign.ts` | `loadCampaignOrThrow()`, `serializeLine()` (includes `agent_id`, `sku`). |
| `lib/sync-auth.ts` | `verifySyncAuth(headers, rawBody)` — Bearer token + `X-Timestamp` (±5 min) + `X-Signature` HMAC. Gate on every `/api/sync/*` route. |
| `lib/sync-validation.ts` | zod schemas for each inbound sync payload (campaign, warehouses, items, agents, recount). |
| `lib/client.ts` | **Browser-side** `api.*` helpers (login, logout, me, items, mine, recount, submit). Same-origin cookies ride along automatically. |

---

## 3. Pages (all wired to the API)

| Route | What the field user does |
|-------|--------------------------|
| `/c/{campaign}/a/{token}` | Magic-link landing — pre-fills the token, prompts for PIN. |
| `/login` | Manual token + PIN entry (`LoginForm`). On success → `/my-campaign`. |
| `/my-campaign` | Shows the agent, campaign window state, and assigned warehouses. |
| `/count` | Count entry — `CountTable` with unit/pack inputs, **add item not in list**, per-row Save. |
| `/recount` | Only the lines flagged for re-count (highlighted amber); re-submit. |
| `/progress` | Counted vs flagged progress for the agent. |

`components/CountTable.tsx` saves **per item, per row** (each Save calls `POST /api/counts`,
creating a line with a fresh `line_uid` or bumping `version` on edit). Flagged lines render with an
amber background. `components/Shell.tsx` is the layout `// DESIGN-SLOT` for the user's design system.

---

## 4. Authentication (field side)

1. CDG generates credentials in gestion; the **token + PIN hash** are pushed to the public DB.
2. Agent opens the magic link → enters the 4-digit PIN.
3. `POST /api/auth/login` checks: token exists + active, not expired, **campaign window open**
   (else `423`), not locked out (`429` after `LOGIN_MAX_PIN_ATTEMPTS`, default 5), and PIN matches
   the bcrypt hash. Failed attempts increment `failed_attempts`; success resets it.
4. On success a **signed, httpOnly** session cookie (`ama_session`, HMAC-signed, 12h) scoped to
   `(agentId, campaignId)` is set. All field routes call `requireSession()`.

The agent's device never receives any stock figure, and the credential is dead the moment the
campaign window closes or CDG revokes it. See [08 · Security](08-security.md).

---

## 5. The two kinds of API route

The public app exposes **two distinct API surfaces** — do not confuse them:

- **Field API** (`/api/auth/*`, `/api/me`, `/api/items`, `/api/counts*`, `/api/recount`) — used by
  the **agent's browser**, gated by the session cookie + the campaign window.
- **Sync API** (`/api/sync/*`) — used **only by the gestion backend**, gated by HMAC service-token
  auth (`verifySyncAuth`). This is the receiving end of the outbound channel.

Every route exports `dynamic = "force-dynamic"` (no static caching of authenticated data). Full
contracts in [04 · API reference](04-api-reference.md).

---

## 6. Local dev database & seed

- `public-app/docker-compose.yml` runs a local Postgres on **port 5433**, user `ama`, db
  `public_app` (the name `public` is a reserved Postgres role — hence `ama`).
- `prisma/seed.ts` loads an **OPEN** demo campaign, 2 warehouses, 3 items, agent `AG-1001`, and a
  credential `token="demo-token"` / PIN `1234` (bcrypt hash). Lets you log in and count immediately.

---

## 7. Tests

`tests/` (vitest):
- `window.test.ts` — campaign-window open/closed logic.
- `sync-auth.test.ts` — HMAC token/timestamp/signature verification.
- `auth.test.ts` — login validation, lockout, PIN verify.
</content>
