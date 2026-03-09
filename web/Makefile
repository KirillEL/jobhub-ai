PYTHON ?= python3

.PHONY: install dev build check compose-up compose-down compose-logs

install:
	npm install

dev:
	npm run dev -- --host 0.0.0.0 --port 5173

build:
	npm run build

check:
	npm run lint

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f web
