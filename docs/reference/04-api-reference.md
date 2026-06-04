# 04 · API Reference

[← Documentation index](../DOCUMENTATION.md)

Three API surfaces exist:

1. **Gestion API** (Django/DRF) — staff UI, session + group auth. *Mostly Phase 6–7; today it
   exposes health + admin and is the include point for upcoming viewsets.*
2. **Public field API** (Next.js) — the agent's browser, session-cookie auth + campaign window.
3. **Public sync API** (Next.js) — the gestion backend only, HMAC service-token auth.

All errors use the uniform envelope: `{"error": {"code": "<machine_code>", "detail": "<message>"}}`.

---

## 1. Gestion API (Django)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/health/` | none | Liveness probe (used by the Docker healthcheck). |
| — | `/admin/` | Django session | Django admin for all models. |
| — | `/api/...` | session + group | Staff REST viewsets (campaigns, reconciliation, exports) land here in Phases 6–7. |

Default DRF auth = session; default permission = `IsAuthenticated`; role checks via
`IsInventoryResponsible` / `IsAudit` / `IsCDG`. Page size 50.

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
