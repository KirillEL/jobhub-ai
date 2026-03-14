PYTHON ?= python3

.PHONY: install test check compose-up compose-down compose-logs

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	PYTHONPATH=src $(PYTHON) -m pytest

check:
	$(PYTHON) -m compileall src tests

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f parser
