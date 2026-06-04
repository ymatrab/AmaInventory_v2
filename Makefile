# Inventory Platform — task runner.
# Gestion runs entirely in Docker; its targets wrap `docker compose`.
# The public-app (Next.js) runs on the host Node toolchain (targets Vercel),
# with a local Postgres container for dev (separate trust zone from gestion).

COMPOSE := docker compose -f gestion/docker-compose.yml
PUBLIC_COMPOSE := docker compose -f public-app/docker-compose.yml

.PHONY: setup env db migrate seed dev up down test lint e2e clean help

help:
	@echo "Targets: setup db migrate seed dev up down test lint e2e clean"

# Ensure local env files exist (copied from the committed .example templates).
# public-app uses .env (read by both Prisma and Next.js).
env:
	@test -f gestion/.env || cp gestion/.env.example gestion/.env
	@test -f public-app/.env || cp public-app/.env.example public-app/.env

# Build gestion Docker images + install public-app deps + generate Prisma client.
setup: env
	$(COMPOSE) build
	cd public-app && npm install
	$(PUBLIC_COMPOSE) up -d
	cd public-app && npx prisma generate
	@echo "==> setup complete."

# Start datastores: gestion (Postgres + Redis) and the public-app Postgres.
db: env
	$(COMPOSE) up -d postgres redis
	$(PUBLIC_COMPOSE) up -d

# Migrations: gestion (in web container) + public-app (Prisma).
migrate: env
	$(COMPOSE) run --rm web python manage.py migrate
	$(PUBLIC_COMPOSE) up -d
	cd public-app && npx prisma migrate deploy

# Demo seed: gestion (groups/users/warehouses/items/field users) + public OPEN campaign.
seed: migrate
	$(COMPOSE) run --rm web python manage.py seed_demo
	cd public-app && npm run db:seed

# Full dev: gestion stack + public-app Postgres in the background (Docker);
# public-app dev server in the foreground.
dev: env
	$(COMPOSE) up -d
	$(PUBLIC_COMPOSE) up -d
	@echo "==> gestion: API http://127.0.0.1:8000  frontend http://127.0.0.1:5174  | public: http://127.0.0.1:3000"
	cd public-app && npm run dev

up: env
	$(COMPOSE) up -d
	$(PUBLIC_COMPOSE) up -d

down:
	$(COMPOSE) down
	$(PUBLIC_COMPOSE) down

# Tests: gestion (pytest in container) + public-app (vitest).
test: env
	$(COMPOSE) run --rm web pytest -q
	cd public-app && npm test

# Lint/format checks: gestion backend (ruff+black, in container), gestion
# frontend (eslint+prettier+tsc, in container), public-app (host).
lint: env
	$(COMPOSE) run --rm web sh -c "ruff check . && black --check ."
	$(COMPOSE) run --rm frontend sh -c "npm install --no-audit --no-fund --silent && npm run lint"
	cd public-app && npm run lint

# Full end-to-end happy path (implemented in Phase 9).
e2e:
	@echo "==> e2e happy path implemented in Phase 9."

# Stop and remove containers + volumes (wipes local DBs).
clean:
	$(COMPOSE) down -v
	$(PUBLIC_COMPOSE) down -v
