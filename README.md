# Inventory Platform (AmaInventory)

Monthly inventory-control platform — two apps that behave like one product:

- **`gestion/`** — internal app (Inventory Responsible, Audit, CDG). Runs on the company
  local network behind a VPN, has read-only SAP access, owns reconciliation, margins,
  re-counts, CSV export, sign-off, history. **Runs entirely in Docker (dev and prod).**
- **`public-app/`** — internet-facing app for field users (Inventory Agent + Warehouseman)
  who perform the physical count. Hosted on Vercel. **No SAP access, no stock data.**

The gestion backend talks to the public app over **one outbound-only channel** (push config,
pull counts). The public app never calls into the local network. See [`CLAUDE.md`](CLAUDE.md)
§2 for the Golden Rules and [`docs/`](docs/) for the full process and architecture.

## Repository layout

```
.
├── CLAUDE.md                 # operating manual (auto-loaded)
├── BUILD_PLAN.md             # ordered, phase-by-phase build steps
├── docs/                     # business process + system architecture
├── gestion/                  # Django + DRF backend, React (Vite) frontend, Docker stack
├── public-app/               # Next.js (App Router) field app
└── packages/tokens/          # shared design tokens (both frontends consume)
```

## Prerequisites

- **Docker + Docker Compose** (gestion runs fully in Docker — no host Python/Postgres needed)
- **Node.js 20+** and **npm** (for the public-app and the gestion frontend tooling)

## Quick start

```bash
make setup     # build gestion images + install public-app deps
make dev       # start the full gestion Docker stack + public-app dev server
make migrate   # run gestion DB migrations (inside the web container)
make seed      # load demo data
make test      # run gestion + public-app tests
make lint      # run linters/formatters
```

| App | Dev URL |
|-----|---------|
| Gestion API (Django) | http://127.0.0.1:8000 |
| Gestion frontend (Vite) | http://127.0.0.1:5174 |
| Public app (Next.js) | http://127.0.0.1:3000 |

> Gestion service ports are bound to `127.0.0.1` in dev and must only be reachable over the
> local/VPN network in production — never exposed to the internet.

## Build status

Built phase-by-phase per [`BUILD_PLAN.md`](BUILD_PLAN.md). Current: **Phase 0 — scaffolding**.
