PYTHON ?= python3
COMPOSE ?= docker compose
COMPOSE_DEBUG ?= docker compose -f docker-compose.yml -f docker-compose.local.yml

.PHONY: install run-api check migrate migration-new migration-autogen compose-up compose-down compose-logs compose-up-debug compose-down-debug compose-logs-debug

install:
	$(PYTHON) -m pip install -r requirements.txt

run-api:
	PYTHONPATH=src uvicorn parser_api.main:app --reload --host 0.0.0.0 --port 8000

check:
	$(PYTHON) -m compileall src alembic

migrate:
	PYTHONPATH=src alembic upgrade head

migration-new:
	PYTHONPATH=src alembic revision -m "$(m)"

migration-autogen:
	PYTHONPATH=src alembic revision --autogenerate -m "$(m)"

compose-up:
	$(COMPOSE) up -d postgres
	$(COMPOSE) run --rm api sh -c "PYTHONPATH=src alembic upgrade head"
	$(COMPOSE) up -d --build parser api

compose-down:
	$(COMPOSE) down

compose-logs:
	$(COMPOSE) logs -f api parser postgres

compose-up-debug:
	$(COMPOSE_DEBUG) up -d postgres
	$(COMPOSE_DEBUG) run --rm api sh -c "PYTHONPATH=src alembic upgrade head"
	$(COMPOSE_DEBUG) up -d --build parser api

compose-down-debug:
	$(COMPOSE_DEBUG) down

compose-logs-debug:
	$(COMPOSE_DEBUG) logs -f api parser postgres
