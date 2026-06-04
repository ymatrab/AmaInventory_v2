# 00 · Architecture & Trust Zones

[← Documentation index](../DOCUMENTATION.md)

This document is the map. It shows the two apps, the security boundary between them, and how a
count flows end-to-end. Every other reference doc zooms into one box on this map.

---

## 1. The two apps and the boundary

```
        TRUST ZONE: LOCAL / VPN                       TRUST ZONE: PUBLIC INTERNET
 ┌───────────────────────────────────────┐     ┌──────────────────────────────────────┐
 │                gestion/                 │     │              public-app/             │
 │                                         │     │                                      │
 │  React (Vite) SPA  ──►  Django + DRF    │     │   Next.js pages ──► Next.js API      │
 │   (staff UI)            (web container) │     │   (field UI)        routes           │
 │                          │              │     │                      │               │
 │                          ▼              │     │                      ▼               │
 │  Celery worker + beat   PostgreSQL      │     │                  PostgreSQL          │
 │   (sync poller/jobs)    (gestion DB)    │     │                  (public DB)         │
 │        │                                │     │                                      │
 │        │   read-only                    │     │   NO SAP. NO STOCK. NO VALUES.       │
 │        ▼                                │     │                                      │
 │  SAP (read-only seam) ◄─ MockSapClient  │     │                                      │
 │                          RealSapClient  │     │                                      │
 └───────────────┬─────────────────────────┘     └───────────────▲──────────────────────┘
                 │                                                │
                 │   ════════  OUTBOUND ONLY  ════════►          │
                 │   gestion ALWAYS initiates (push + pull)       │
                 └───────────────────────────────────────────────┘
                     The public app NEVER calls into the local zone.
```

**Key invariant:** the arrow only ever points right. The local zone exposes **no inbound port** to
the public app. The public app does not know any gestion address, route, or secret that would let
it reach in.

---

## 2. What each box is, and where it's documented

| Box | Tech | Container/host | Detail doc |
|-----|------|----------------|------------|
| Django + DRF web | Django 5, DRF | `web` container | [02 · Gestion backend](02-gestion-backend.md) |
| Gestion PostgreSQL | Postgres 16 | `postgres` container | [01 · Data model](01-data-model.md) |
| Celery worker / beat | Celery + Redis | `celery`, `beat` containers | [05 · Sync connector](05-sync-connector.md) |
| Redis (broker) | Redis 7 | `redis` container | [07 · Tooling & ops](07-tooling-and-ops.md) |
| Gestion React SPA | React + Vite + TS | `frontend` container | [02 · Gestion backend](02-gestion-backend.md) §frontend *(scaffold; full SPA = Phase 7)* |
| SAP connector | Python seam | inside `web`/`celery` | [06 · SAP connector](06-sap-connector.md) |
| Sync client | `requests` + HMAC | inside `web`/`celery` | [05 · Sync connector](05-sync-connector.md) |
| Next.js field app | Next.js App Router | Vercel (host Node in dev) | [03 · Public app](03-public-app.md) |
| Public PostgreSQL | Postgres (Neon/Supabase in prod) | `public-app/docker-compose.yml` in dev | [01 · Data model](01-data-model.md) |
| Shared design tokens | CSS vars | `packages/tokens/` | [07 · Tooling & ops](07-tooling-and-ops.md) |

---

## 3. End-to-end data flow (the happy path)

This is the lifecycle the whole system is built to serve. Steps marked **→** cross the boundary
(always gestion-initiated).

1. **Create campaign** (gestion, Audit/CDG) — a `Campaign` row, scoped to warehouses, with a
   counting window (`open_at`/`close_at`).
2. **Arm campaign** (gestion) — `snapshot_system_stock()` reads SAP (mock today) and freezes a
   `SystemStock` snapshot per (warehouse, item). The window/snapshot is now stable.
3. **Generate credentials** (gestion) — `generate_credentials()` mints a per-agent token + 4-digit
   PIN; only the **bcrypt hash** of the PIN is stored.
4. **→ Push setup** (gestion → public) — `push_campaign_setup()` sends campaign window,
   warehouses, item **reference** (no quantities), and agents (matricule + token + PIN hash).
5. **Confirm (Audit)** — assignment list confirmed; campaign opens.
6. **Agent logs in** (public) — opens magic link `/c/{campaign}/a/{token}`, enters PIN. Validated
   against the campaign window + lockout; a signed, httpOnly session cookie is issued.
7. **Agent counts** (public) — submits count lines (units/packs). Each line gets a stable
   `line_uid` (UUID) and a `version`; edits bump the version. **Only what was physically counted
   is stored** — never system stock.
8. **→ Pull counts** (gestion ← public) — Celery beat (`poll_open_campaigns`) periodically calls
   `pull_counts()`, walking a compound cursor `updated_at|line_uid`. Lines are **upserted by
   `line_uid`+`version`** — re-polling never duplicates.
9. **Reconcile (CDG)** *(Phase 6)* — join pulled counts with `SystemStock`, compute `gap_qty` and
   `gap_value`, set a monetary `value_margin` per warehouse.
10. **→ Flag re-count** (gestion → public) — `push_recount()` flags items; the campaign enters
    `RECOUNT`; the agent re-submits flagged lines (new `Count` with `is_recount=True`).
11. **CSV export** *(Phase 6)* — generate the CSV for separate SAP import (mapping is a seam).
12. **Close campaign** — window closes, tokens expire, history is preserved; later `ARCHIVED`.

The campaign status machine: `DRAFT → ARMED → OPEN → RECOUNT → CLOSED → ARCHIVED` (mirrored on
both sides; the public side only ever receives the status, never sets it).

---

## 4. Why the boundary is shaped this way

- **The local zone is the only place stock exists.** SAP, system quantities, costs, gaps, and
  margins are commercially sensitive. If the public app were breached, there is simply nothing
  there to leak — its schema has no columns for it (see [01 · Data model](01-data-model.md) §3).
- **Outbound-only removes the attack surface.** No inbound port to the VPN means the public app
  cannot be turned into a pivot into the corporate network, regardless of how it's compromised.
- **The agent's device is untrusted.** Auth is short-lived (campaign window), per-agent, and
  revocable; the device never holds long-term credentials or any stock figure to compare against.

See [08 · Security model](08-security.md) for how each of these is enforced in code.
</content>
