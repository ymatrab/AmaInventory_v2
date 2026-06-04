# 08 · Security Model

[← Documentation index](../DOCUMENTATION.md)

The security design is the product. This document shows **where each Golden Rule is enforced in
code**, so you can verify it rather than trust it.

---

## 1. Trust zones

| Zone | Contains | Reachable from |
|------|----------|----------------|
| **Local / VPN** | gestion (Django, Postgres, Redis, Celery), SAP, all stock/values/margins | the company network only |
| **Public internet** | public-app (Next.js, Postgres), counts, item reference, agent logins | anyone (it's on Vercel) |

The boundary between them is crossed by **exactly one** actor — the gestion sync client — in
**exactly one** direction — outbound.

---

## 2. Golden Rule §1 — outbound-only

**Rule:** gestion initiates every cross-boundary call; the public app never calls in; no inbound
port to the local zone.

**Enforced by:**
- `apps/sync/client.py` is the only code that crosses the boundary, and it only ever makes
  **outbound** `requests` calls to `PUBLIC_API_BASE_URL`.
- The public app has **no** gestion address, route, or credential. Its `lib/client.ts` only calls
  its own same-origin `/api/*`.
- Gestion Docker ports bind to `127.0.0.1` in dev / the private interface behind the VPN in prod
  ([07 · Tooling](07-tooling-and-ops.md) §3). Nothing on the public side can reach them.
- There is **no** webhook/endpoint on the gestion side that the public app calls.

**To verify:** grep the public app for any gestion URL or for outbound calls to a private host —
there are none. The only inbound-from-internet surface gestion has is *nothing*; it is pull-based.

---

## 3. Golden Rule §2 — no stock leaves the local zone

**Rule:** the public DB never stores system quantities, costs, values, gaps, or margins.

**Enforced by:**
- The public Prisma schema (`prisma/schema.prisma`) **has no columns** for any of these
  ([01 · Data model](01-data-model.md) §3). `count_line` holds only what was physically counted;
  `item_ref` holds only reference attributes.
- The sync **push payloads** are an exhaustive whitelist of non-sensitive fields
  ([05 · Sync connector](05-sync-connector.md) §2) — `system_qty`/`unit_value`/gaps/margins are
  never in them.
- `SystemStock`, `Reconciliation*`, and margins live **only** in the gestion DB.

**Planned (Phase 8):** an automated test asserting the public schema contains none of the forbidden
columns, so a future migration can't accidentally add one.

---

## 4. Golden Rule §3 — secrets never in the repo

**Enforced by:**
- Only `.env.example` templates are committed; real `.env`/`.env.local` are gitignored.
- `make env` materializes local env files from the templates.
- Shared secrets (`SYNC_SERVICE_TOKEN`, `SYNC_HMAC_SECRET`, `SESSION_SECRET`, `DJANGO_SECRET_KEY`,
  `SAP_*`) are env-only on both sides.

---

## 5. Golden Rule §4 — SAP/CSV are seams

See [06 · SAP connector](06-sap-connector.md). The real connector is isolated in `apps/sap/`,
read-only, and inert until wired. The CSV-to-SAP mapping is a `# SEAM` (Phase 6).

---

## 6. Golden Rule §5 — field auth is per-agent and time-boxed

**Rule:** login = unique link + PIN, valid only during the campaign window, revocable, always
attributed to an agent.

**Enforced by:**

| Property | Where |
|----------|-------|
| Unique per-agent link | `AgentCredential.token` (gestion) → pushed to public; magic link `/c/{campaign}/a/{token}`. |
| PIN, hashed only | gestion stores **bcrypt hash** only (`generate_credentials`); plaintext shown once at generation. Public verifies via `bcryptjs` (`lib/pin.ts`). |
| Time-boxed to the window | `lib/window.ts::isCampaignOpen()` checks status + `open_at`/`close_at`; login returns **423** when closed; every field route calls `assertCampaignOpen()`. |
| Revocable / expirable | `AgentCredential.active` + `expires_at`; login rejects inactive/expired. |
| Lockout | `failed_attempts` increments on bad PIN; **429** after `LOGIN_MAX_PIN_ATTEMPTS` (default 5); reset on success. |
| Always attributed | every `count_line` carries `agent_id`; the session cookie is scoped to `(agentId, campaignId)`. |
| Session integrity | `lib/session-crypto.ts` signs the cookie `base64url(payload).base64url(HMAC-SHA256)`, timing-safe verify; cookie is **httpOnly**, sameSite lax, secure in prod, 12h. |

---

## 7. The sync channel's own auth

Even though it's outbound, the receiving `/api/sync/*` endpoints are hardened
([05 · Sync connector](05-sync-connector.md) §1):
- **Bearer service token** (timing-safe compare),
- **`X-Timestamp`** within ±5 minutes (anti-replay),
- **`X-Signature`** = HMAC-SHA256 of the raw body (forgery-proof).

A captured request can't be replayed (timestamp) and a tampered body fails the signature.

---

## 8. Hardening still to come (Phase 8)

Tracked in [09 · Status](09-status-and-roadmap.md): Cloudflare-ready security headers, rate limits
on login + sync, strict CORS, service-token rotation (two valid keys during rotation), VPN-only
binding docs, full audit-log coverage review, the automated "no stock columns" schema assertion,
and a secrets review. These harden an already-correct boundary; they don't change the model above.
</content>
