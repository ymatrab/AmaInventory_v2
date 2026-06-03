# Inventory Platform — task runner.
# Gestion runs entirely in Docker; its targets wrap `docker compose`.
# The public-app (Next.js) runs on the host Node toolchain (targets Vercel).

COMPOSE := docker compose -f gestion/docker-compose.yml

.PHONY: setup env db migrate seed dev up down test lint e2e clean help

help:
	@echo "Targets: setup db migrate seed dev up down test lint e2e clean"

# Ensure local env files exist (copied from the committed .example templates).
env:
	@test -f gestion/.env || cp gestion/.env.example gestion/.env
	@test -f public-app/.env.local || cp public-app/.env.example public-app/.env.local

# Build gestion Docker images + install public-app deps on the host.
setup: env
	$(COMPOSE) build
	cd public-app && npm install
	@echo "==> setup complete."

# Start just the datastores (Postgres + Redis) in the background.
db: env
	$(COMPOSE) up -d postgres redis

# Run gestion DB migrations inside the web container.
migrate: env
	$(COMPOSE) run --rm web python manage.py migrate

# Demo seed: groups, one user per group, demo warehouses/items/field users.
seed: migrate
	$(COMPOSE) run --rm web python manage.py seed_demo

# Full dev: gestion stack (web, frontend, postgres, redis, celery, beat) in the
# background via Docker; public-app dev server in the foreground.
dev: env
	$(COMPOSE) up -d
	@echo "==> gestion up: API http://127.0.0.1:8000  frontend http://127.0.0.1:5174"
	cd public-app && npm run dev

up: env
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

# Tests: gestion (pytest in container) + public-app.
test: env
	$(COMPOSE) run --rm web pytest -q
	@echo "==> public-app tests: none yet (added in later phases)."

# Lint/format checks: gestion backend (ruff+black, in container), gestion
# frontend (eslint+prettier+tsc, in container), public-app (host).
lint: env
	$(COMPOSE) run --rm web sh -c "ruff check . && black --check ."
	$(COMPOSE) run --rm frontend sh -c "npm install --no-audit --no-fund --silent && npm run lint"
	cd public-app && npm run lint

# Full end-to-end happy path (implemented in Phase 9).
e2e:
	@echo "==> Phase 0: e2e happy path implemented in Phase 9."

# Stop and remove containers + volumes (wipes local DB).
clean:
	$(COMPOSE) down -v
