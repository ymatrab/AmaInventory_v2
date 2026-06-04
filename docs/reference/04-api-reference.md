# 04 · API Reference

[← Documentation index](../DOCUMENTATION.md)

Three API surfaces exist:

1. **Gestion API** (Django/DRF) — staff UI, session + group auth. *Mostly Phase 6–7; today it
   exposes health + admin and is the include point for upcoming viewsets.*
2. **Public field API** (Next.js) — the agent's browser, session-cookie auth + campaign window.
3. **Public sync API** (Next.js) — the gestion backend only, HMAC service-token auth.

All errors use the uniform envelope: `{"error": {"code": "<machine_code>", "detail": "<message>"}}`.

---

## 1. Gestion API (Django) — auth = session cookie + CSRF

The SPA reaches this API **same-origin** through the Vite dev proxy, so the session cookie and CSRF
token work without cross-origin cookie pain. Default DRF auth = session; default permission =
`IsAuthenticated`; page size 50; uniform error envelope. The SPA additionally **hides/disables**
actions by role (`is_cdg` / `is_audit` / `is_inventory_responsible` from `/api/auth/me/`).

### Session
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health/` | Liveness probe (Docker healthcheck), no auth. |
| GET | `/api/auth/csrf/` | Sets the `csrftoken` cookie before login. |
| POST | `/api/auth/login/` | `{username, password}` → Django session; returns the user + role flags. |
| POST | `/api/auth/logout/` | Ends the session. |
| GET | `/api/auth/me/` | Current user `{username, groups, is_cdg, is_audit, is_inventory_responsible, …}`. |
| — | `/admin/` | Django admin for all models. |

### Domain (DRF router)
| Resource | Endpoints |
|----------|-----------|
| Campaigns | `GET/POST /api/campaigns/`, `GET /api/campaigns/{id}/`; actions `POST {id}/arm`, `generate_credentials`, `push_setup`, `open`, `close`, `extend`, `sync_now`. |
| Assignments | `GET/POST /api/assignments/?campaign=`, `DELETE {id}`, `POST /api/assignments/confirm/` (Audit). |
| Warehouses / Items / Field users | `GET/POST /api/warehouses/`, `/api/items/`, `GET /api/field-users/`. |
| Counts (monitoring) | `GET /api/counts/?campaign=&warehouse=&agent=`; `GET /api/counts/monitor/?campaign=`; `GET /api/counts/kpi/?campaign=`. |
| Reconciliation | `GET /api/reconciliations/?campaign=`; actions `POST /api/reconciliations/build/`, `set_margin/`, `flag_recount/`. |
| CSV exports | `GET /api/exports/?campaign=`; `POST /api/exports/generate/`; `GET /api/exports/{id}/download/` (streams the CSV). |
| Sign-off | `GET/POST/PATCH /api/signoffs/?campaign=`. |
| Audit log | `GET /api/audit/?entity=&entity_id=`. |

Lifecycle/reconciliation actions are thin wrappers over the services in
[02 · Gestion backend](02-gestion-backend.md). The Phase-1 endpoints `/api/whoami/` and
`/api/cdg-only/` remain for backward compatibility.

---

## 2. Public Field API (Next.js) — auth = signed session cookie `ama_session`

All routes are `force-dynamic`. Unless noted, a missing/invalid session → `401`; a closed campaign
window → `423`.

### `POST /api/auth/login`
Body `{ token, pin }`. Validates token active + not expired + window open + not locked out + PIN
matches bcrypt hash.

- **200** `{ ok: true, agent: { id, full_name, role }, campaign_id }` and sets the `ama_session`
  cookie (httpOnly, sameSite lax, secure in prod, 12h).
- **401** `invalid_login` (bad token/PIN; message includes remaining attempts) / **401** `expired`.
- **423** `campaign_closed` (no active window).
- **429** `locked` (≥ `LOGIN_MAX_PIN_ATTEMPTS`, default 5).

### `POST /api/auth/logout`
Clears the cookie. **200** `{ ok: true }`.

### `GET /api/me`
- **200** `{ agent: {id, full_name, role}, campaign: {code, status, open}, warehouses: [{id, whs_code, name}] }`.

### `GET /api/items`
The item reference for the campaign (no quantities).
- **200** `{ items: [{ item_code, sku, description, color_parfum, units_per_pack }] }`.

### `POST /api/counts`
Create or update a count line. Body = `countSubmitSchema`:
`{ line_uid?, warehouse_id, item_code, sku, qty_units, qty_packs }`.
- With `line_uid` → updates that line (must belong to the session agent), **`version` += 1** → **200** `{ line }`.
- Without `line_uid` → creates a new line with a fresh UUID; `is_recount` set if campaign status is
  `RECOUNT` → **201** `{ line }`.
- **400** `invalid_warehouse` (warehouse not in campaign) / **404** `line_not_found`.
- `line` shape (`serializeLine`): `{ line_uid, warehouse_id, item_code, sku, qty_units, qty_packs, agent_id, is_recount, flagged, version }`.

### `GET /api/counts/mine`
- **200** `{ lines: CountLineDTO[], progress: { total, flagged } }` for the session agent.

### `GET /api/recount`
Only the agent's lines flagged for re-count.
- **200** `{ lines: CountLineDTO[] }`.

---

## 3. Public Sync API (Next.js) — auth = `verifySyncAuth` (gestion only)

**Every** `/api/sync/*` request must carry (Appendix B contract):

```
Authorization: Bearer <SYNC_SERVICE_TOKEN>
X-Timestamp:   <unix seconds>            # rejected if skew > 5 min
X-Signature:   hex( HMAC_SHA256(rawBody, SYNC_HMAC_SECRET) )   # body = "" for GET
```

Failure → **401** `bad_token` / `stale_timestamp` / `bad_signature`, or **500** `sync_not_configured`
if secrets are unset. These are the **only** endpoints the gestion backend calls; the public app
never calls gestion.

### Push (gestion → public), all `POST`

| Path | Body | Effect |
|------|------|--------|
| `/api/sync/campaign` | `{ id, code, status, open_at, close_at }` | Upsert the campaign mirror + window. |
| `/api/sync/warehouses` | `[{ id, whs_code, name, city, campaign_id }]` | Upsert campaign warehouses. |
| `/api/sync/items` | `[{ item_code, sku, description, color_parfum, base_unit, units_per_pack, campaign_id }]` | Upsert item **reference** (no quantities). |
| `/api/sync/agents` | `[{ agent_id, full_name, role, token, pin_hash, campaign_id, expires_at }]` | Upsert agents + credentials (PIN **hash** only). |
| `/api/sync/recount` | `{ campaign_id, line_uids?, item_codes? }` | Flag lines/items for re-count; campaign enters `RECOUNT`. |

### Pull (gestion ← public)

**`GET /api/sync/counts?campaign={id}&since={cursor}&limit={n}`** (n clamped 1–500, default 200)

Returns count lines changed since the cursor, ordered `(updated_at ASC, line_uid ASC)`.

- **200** `{ lines: [{ line_uid, warehouse_id, item_code, sku, qty_units, qty_packs, agent_id, is_recount, flagged, version }], next_cursor: "<iso>|<line_uid>" | null }`.

The **compound cursor** `iso8601|line_uid` ensures rows sharing a timestamp are never skipped.
Gestion upserts by `line_uid` + `version`, so re-fetching the same page is harmless (idempotent).
See [05 · Sync connector](05-sync-connector.md) for the full algorithm.
</content>
