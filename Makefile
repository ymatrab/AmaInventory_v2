# AmaInventory — public field counting app (Next.js, Vercel).
# The gestion / internal app lives in the separate AmaFinance repo.
# Prerequisites: Node 20+, Docker + Docker Compose (for the local Postgres).

PUBLIC_COMPOSE := docker compose -f public-app/docker-compose.yml

.PHONY: setup env db migrate seed dev test lint help

help:
	@echo "Targets: setup env db migrate seed dev test lint"

# Ensure local .env exists (copied from the committed .env.example template).
env:
	@test -f public-app/.env || cp public-app/.env.example public-app/.env

# Install deps + generate Prisma client + start local Postgres.
setup: env
	$(PUBLIC_COMPOSE) up -d
	cd public-app && npm install
	cd public-app && npx prisma generate
	@echo "==> setup complete. Run: make seed"

# Start local Postgres container only.
db: env
	$(PUBLIC_COMPOSE) up -d

# Run Prisma migrations against local Postgres.
migrate: env
	$(PUBLIC_COMPOSE) up -d
	cd public-app && npx prisma migrate deploy

# Seed demo data (open campaign for the field agents).
seed: migrate
	cd public-app && npm run db:seed

# Run the Next.js dev server (http://127.0.0.1:3000).
dev: env
	$(PUBLIC_COMPOSE) up -d
	@echo "==> public app: http://127.0.0.1:3000"
	cd public-app && npm run dev

# Run tests (vitest).
test: env
	cd public-app && npm test

# Lint (eslint + tsc).
lint: env
	cd public-app && npm run lint

# Stop containers and wipe volumes.
clean:
	$(PUBLIC_COMPOSE) down -v
