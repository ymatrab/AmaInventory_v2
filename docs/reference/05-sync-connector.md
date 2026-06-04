# 05 · Sync Connector & Contract

[← Documentation index](../DOCUMENTATION.md)

The single channel between the two apps. **Gestion always initiates** (Golden Rule §1). It does two
things: **push** campaign setup out, and **pull** counts in. Both are plain outbound HTTPS.

- Gestion side: `apps/sync/` (`client.py`, `services.py`, `tasks.py`, `models.py`).
- Public side: `app/api/sync/*` + `lib/sync-auth.ts` + `lib/sync-validation.ts`.

---

## 1. Authentication (Appendix B)

Every request the gestion `SyncClient` makes carries three headers, verified by the public
`verifySyncAuth`:

| Header | Value | Verified by |
|--------|-------|-------------|
| `Authorization` | `Bearer <SYNC_SERVICE_TOKEN>` | timing-safe compare against the shared token |
| `X-Timestamp` | unix seconds at send | rejected if `|now − ts| > 5 min` (anti-replay) |
| `X-Signature` | `hex(HMAC_SHA256(rawBody, SYNC_HMAC_SECRET))` | recomputed over the raw body; for GET the body is `""` |

Both `SYNC_SERVICE_TOKEN` and `SYNC_HMAC_SECRET` are shared secrets, provided via env on both
sides, never committed. The signature is over the **exact serialized body** (gestion uses compact
`json.dumps(payload, separators=(",", ":"))` so both sides hash identical bytes).

```python
# gestion/backend/apps/sync/client.py
signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
headers = {"Authorization": f"Bearer {token}", "X-Timestamp": str(int(time.time())),
           "X-Signature": signature, "Content-Type": "application/json"}
```

```ts
// public-app/lib/sync-auth.ts
const expected = createHmac("sha256", secret).update(rawBody).digest("hex");
if (!safeEqual(signature, expected)) throw new ApiError(401, "bad_signature", ...);
```

---

## 2. Push — `SyncClient` + `push_campaign_setup()`

`apps/sync/services.py::push_campaign_setup(campaign, client, items)` calls, in order:

1. `push_campaign(campaign)` → `POST /api/sync/campaign` — id, code, status, window.
2. `push_warehouses(campaign)` → `POST /api/sync/warehouses` — the campaign's warehouses.
3. `push_items(campaign, items)` → `POST /api/sync/items` — item **reference only** (code, sku,
   description, color/parfum, base_unit, units_per_pack). **No quantities are ever in this payload.**
4. `push_agents(campaign)` → `POST /api/sync/agents` — for each credential: matricule, name, role,
   token, **pin_hash** (never the plaintext PIN), expiry.

`push_recount(campaign, line_uids=, item_codes=)` → `POST /api/sync/recount` is called separately
during reconciliation to flag items and move the campaign into `RECOUNT`.

What is **deliberately never pushed:** system quantities, unit values, gaps, margins, anything from
SAP. The push payloads above are the complete list of fields that cross the boundary.

---

## 3. Pull — idempotent, cursor-based

`apps/sync/services.py::pull_counts(campaign, client)`:

```
cursor ← SyncCursor.cursor for this campaign  (empty = from the beginning)
loop:
    page ← GET /api/sync/counts?campaign=&since=cursor&limit=200
    for line in page.lines:  upsert_count_line(campaign, line)
    cursor ← page.next_cursor   # persisted after every page
    stop when the page returns fewer than PAGE_SIZE rows
```

### The compound cursor
The public side orders by `(updated_at ASC, line_uid ASC)` and returns
`next_cursor = "<updated_at ISO>|<line_uid>"`. On the next request it resumes with:

```
updatedAt > cursorTime  OR  (updatedAt == cursorTime AND lineUid > cursorUid)
```

This is why the cursor is **compound**: many lines can share the same `updated_at`; keying on time
alone would skip or repeat rows. The `(campaign_id, updated_at)` index backs this scan.

### Idempotent upsert — `upsert_count_line(campaign, line)`
The heart of "never duplicate on re-poll":

1. If a `CountLine` with this `line_uid` already exists **and its `version` ≥ incoming version** →
   **skip** (return `False`). Re-fetching the same or older data is a no-op.
2. Resolve the warehouse (by pk) and item (by `item_code`+`sku`). If either is unmapped → skip with
   a warning.
3. Resolve the agent by `matricule` (for KPI attribution).
4. `get_or_create` the parent `Count` (`is_recount` distinguishes the original vs re-count copy).
5. `update_or_create` the `CountLine` keyed on `line_uid`, writing qty/packs/version/flag; the
   model recomputes `total_units`.
6. Stamp `count.synced_at`.

Because the key is `line_uid` and the guard is `version`, a crashed pull can be retried from the
last persisted cursor with zero risk of duplicates or lost updates.

---

## 4. Scheduling — Celery beat

`config/settings.py` registers a beat task every `SYNC_POLL_SECONDS` (default 120s):

```python
CELERY_BEAT_SCHEDULE = {"poll-open-campaigns": {
    "task": "apps.sync.tasks.poll_open_campaigns", "schedule": float(SYNC_POLL_SECONDS)}}
```

- `apps/sync/tasks.py::poll_open_campaigns()` — beat task; pulls every `OPEN`/`RECOUNT` campaign.
- `apps/sync/tasks.py::pull_counts_task(campaign_id)` — on-demand pull for one campaign.
- `SyncCursor` (one row per campaign) stores the bookmark so polling resumes where it left off.

### Manual trigger
```bash
docker compose run --rm web python manage.py sync_now <campaign_id>            # push setup + pull
docker compose run --rm web python manage.py sync_now <campaign_id> --pull-only
```

---

## 5. Why this design is safe

- **Outbound only.** The public app exposes the `/api/sync/*` endpoints, but *gestion* is the one
  that calls them. No port into the local zone is ever opened, so there is no inbound path to
  attack (Golden Rule §1).
- **Authenticated + signed + time-boxed.** Token + HMAC + 5-minute timestamp window means a
  captured request can't be replayed and a forged body fails the signature.
- **Stock never crosses.** The push payloads (§2) are an exhaustive whitelist of non-sensitive
  fields; the pull payload is only what agents physically counted.
</content>
