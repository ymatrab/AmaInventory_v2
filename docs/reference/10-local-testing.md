# 10 · Running & Manually Testing Locally

[← Documentation index](../DOCUMENTATION.md)

How to bring the whole platform up on your machine and click through it by hand. Everything the
gestion side needs runs in Docker; the public app runs on host Node with its own Postgres container.

---

## 1. Prerequisites

- **Docker + Docker Compose** (gestion stack + both Postgres databases)
- **Node.js 20+** and **npm** (public-app dev server)

---

## 2. One-time setup

```bash
make setup     # build gestion images, install public-app deps, prisma generate
make migrate   # gestion (Django) + public (Prisma) migrations
make seed      # demo data on BOTH sides
```

### Shared sync secrets (needed for gestion ↔ public sync)
The two apps authenticate the sync channel with **shared secrets** that must be identical in
`gestion/.env` and `public-app/.env` (these files are gitignored — set them once):

```
# gestion/.env  AND  public-app/.env  — same values on both sides
SYNC_SERVICE_TOKEN=dev-sync-token-...
SYNC_HMAC_SECRET=dev-sync-secret-...
# public-app/.env only
SESSION_SECRET=dev-session-secret-...
```

`make env` creates the files from the templates; fill the three values above (any random strings,
matching across the two SYNC_* entries). `gestion/.env` already defaults
`PUBLIC_API_BASE_URL=http://host.docker.internal:3000` so the gestion container can reach the
public app on the host.

---

## 3. Start everything

```bash
make dev
```

This brings up the full gestion Docker stack (web, frontend, postgres, redis, celery worker, celery
beat) **plus** the public-app Postgres, then runs the public-app dev server in the foreground.

| Service | URL | Notes |
|---------|-----|-------|
| **Gestion SPA** (staff) | http://127.0.0.1:5174 | the internal app — log in here |
| Gestion API | http://127.0.0.1:8000 | DRF; `/admin/` for Django admin |
| **Public app** (field) | http://127.0.0.1:3000 | the agent counting app |

### Logins (from the demo seed)
| App | User | Password / PIN |
|-----|------|----------------|
| Gestion SPA / admin | `cdg`, `audit`, `inv_resp` | `demo12345` |
| Public field app | token `demo-token` | PIN `1234` |

The three gestion users are in different role groups, so the nav and action buttons change per
login (CDG reconciles, Audit confirms/opens, Inventory Responsible assigns).

---

## 4. Manual test tracks

### Track A — Public field app on its own (fastest)
The public app has its own seeded OPEN campaign, so you can test counting immediately.

1. Open http://127.0.0.1:3000 → **Login**. Enter token `demo-token`, PIN `1234`.
   (Or open the magic link `http://127.0.0.1:3000/c/demo-campaign/a/demo-token` to pre-fill the token.)
2. **My campaign** shows your agent + window + assigned warehouse.
3. **Count** — enter units/packs for an item, press **Save** (note the `saved v1`; edit and save
   again → `v2`). Try **Add item not in list**.
4. **Progress** — see counted/flagged totals.
5. Wrong PIN 5× → locked out (proves the lockout). A closed window → login refused (423).

### Track B — Gestion SPA on its own
1. Open http://127.0.0.1:5174 → sign in as `cdg`.
2. **Campaigns** → open the seeded campaign, or **New campaign** (pick warehouses + window).
3. **Campaign detail** tabs:
   - *Lifecycle* — **Arm** (snapshots SAP-mock stock), **Generate credentials** (prints
     matricule + PIN + magic link once), **Open/Close/Extend**, **Sync now**.
   - *Assignment* — assign a field user to a warehouse; as `audit`, **Confirm all**.
   - *Live counts* — per-warehouse progress from pulled data.
   - *Reconciliation* — **Build gaps**, **Set margin** (watch rows flip in/out of margin),
     select items → **Flag for re-count**, **Generate CSV** → **download**.
   - *Sign-off* / *Agent KPI*.
4. **History** — the audit log of every action you just took.

### Track C — The full cross-app flow (gestion drives the public app)
This exercises the whole pipeline end to end:

1. In the gestion SPA, create a campaign and **Assign** a field user to a warehouse; as `audit`,
   **Confirm**.
2. *Lifecycle* → **Arm** → **Generate credentials** (copy the printed PIN + magic link) →
   **Open** → **Push to public**.
3. Open the printed magic link on http://127.0.0.1:3000, log in with that PIN, and **submit counts**.
4. Back in gestion: *Live counts* → **Sync now** (or wait for the Celery-beat poller, every 120 s)
   → the counted lines appear.
5. *Reconciliation* → **Build gaps**, set a margin, **Flag** an item for re-count → the agent sees
   it flagged on the public app and re-submits → **Sync now** again.
6. **Generate CSV** and **download** it. **Close** the campaign → the agent's login stops working.

---

## 5. Verifying / inspecting

```bash
# Service health
curl -s -o /dev/null -w "gestion %{http_code}\n" http://localhost:8000/api/health/
curl -s -o /dev/null -w "public  %{http_code}\n" http://localhost:3000/

# What the public DB holds (must be NO stock/value/margin columns — Golden Rule §2)
docker compose -f public-app/docker-compose.yml exec postgres \
  psql -U ama -d public_app -c "\d count_line"

# Gestion DB (Django shell)
docker compose -f gestion/docker-compose.yml run --rm web python manage.py shell

# Tail logs
docker compose -f gestion/docker-compose.yml logs -f web celery beat
```

Run the test suites any time: `make test` (37 gestion + 18 public). Lint: `make lint`.

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `push_setup` / `sync_now` fails 401 | `SYNC_*` secrets differ between `gestion/.env` and `public-app/.env`. Make them identical, restart. |
| Gestion SPA can't reach the API | The Vite proxy targets the `web` container; ensure `make dev` is up. Hard-refresh to re-fetch the CSRF cookie. |
| Push from gestion can't reach public | `PUBLIC_API_BASE_URL` must be `http://host.docker.internal:3000` (the host, from inside the container). |
| Public login says "campaign closed" (423) | The campaign window isn't open. Open it in gestion (*Lifecycle* → Open) or use the public seed campaign. |
| Port already in use | Gestion frontend is on 5174 (5173 was taken); public on 3000; gestion API on 8000; DBs on 5432 / 5433. |
| Reset everything | `make clean` (drops DB volumes), then `make migrate && make seed`. |

> All gestion ports bind to `127.0.0.1` only. In production they must sit behind the VPN; the public
> app is the only internet-facing piece (see [08 · Security](08-security.md)).
</content>
