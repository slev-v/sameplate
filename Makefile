.DEFAULT_GOAL := help

DC ?= docker compose

TEST_DC = env POSTGRES_USER=test_user POSTGRES_PASSWORD=test_password POSTGRES_DB=sameplate_test $(DC) --profile test

export MESSAGE

.PHONY: help build up down logs ps migrate revision seed test test-stop lint format-check format check

help:
	@printf '%s\n' \
	  'Development (create .env from .env.example first):' \
	  '  make up                 Build and start backend and database' \
	  '  make build              Build the backend image' \
	  '  make down               Remove dev/test containers; keep dev database volume' \
	  '  make logs               Follow backend logs' \
	  '  make ps                 Show dev/test containers' \
	  '  make migrate            Apply dev database migrations' \
	  '  make revision MESSAGE="description"  Generate a migration for review' \
	  '  make seed               Populate an empty dev recipe catalog' \
	  '' \
	  'Checks (Docker only; no local Python or .env required):' \
	  '  make test               Build, migrate db-test and run pytest' \
	  '  make test-stop          Stop db-test and discard its temporary data' \
	  '  make lint               Check Python code with Ruff' \
	  '  make format-check       Check formatting without editing files' \
	  '  make format             Format Python files' \
	  '  make check              Run lint, formatting checks and tests in sequence'

build:
	$(DC) build backend

up:
	$(DC) up --build -d backend

down:
	$(DC) --profile test down

logs:
	$(DC) logs --follow backend

ps:
	$(DC) --profile test ps --all

migrate:
	$(DC) run --build --rm backend alembic upgrade head

revision:
	@test -n "$$MESSAGE" || { printf '%s\n' 'Usage: make revision MESSAGE="describe the change"' >&2; exit 1; }
	$(DC) run --build --rm backend alembic revision --autogenerate -m "$$MESSAGE"

seed:
	$(DC) run --build --rm backend python scripts/seed_recipes.py /sample_data/dev/recipes.json

test:
	$(TEST_DC) run --build --rm tests

test-stop:
	$(TEST_DC) stop db-test

lint:
	$(TEST_DC) run --build --rm --no-deps tests ruff check .

format-check:
	$(TEST_DC) run --build --rm --no-deps tests ruff format --check .

format:
	$(TEST_DC) run --build --rm --no-deps tests ruff format .

check:
	$(MAKE) lint
	$(MAKE) format-check
	$(MAKE) test
