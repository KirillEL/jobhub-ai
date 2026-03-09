PYTHON ?= python3

.PHONY: install run-parse run-analyze run-report send-alert run-scheduler test check postgres-up postgres-down compose-up compose-down compose-logs compose-report compose-alert

install:
	$(PYTHON) -m pip install -r requirements.txt

run-parse:
	PYTHONPATH=src $(PYTHON) -m vacancy_parser.cli parse --query "python backend" --pages 2

run-analyze:
	PYTHONPATH=src $(PYTHON) -m vacancy_parser.cli analyze --query "python backend" --pages 2

run-report:
	PYTHONPATH=src $(PYTHON) -m vacancy_parser.cli report --limit 500

send-alert:
	PYTHONPATH=src $(PYTHON) -m vacancy_parser.cli alert --limit 200

run-scheduler:
	PYTHONPATH=src $(PYTHON) -m vacancy_parser.cli scheduler

test:
	PYTHONPATH=src $(PYTHON) -m pytest

check:
	$(PYTHON) -m compileall src tests

postgres-up:
	docker compose up -d postgres

postgres-down:
	docker compose down

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f app

compose-report:
	docker compose run --rm app python -m vacancy_parser.cli report --limit 500

compose-alert:
	docker compose run --rm app python -m vacancy_parser.cli alert --limit 200
