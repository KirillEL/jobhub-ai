# Vacancy Parser

Structured Python project for collecting vacancies, storing them, and running analytics.

## Goals

- Parse vacancies from one or more sources.
- Store raw and normalized data.
- Build reusable analytics metrics.
- Provide a clean CLI entrypoint.

## Project Layout

- `src/vacancy_parser/config.py` - app settings and constants.
- `src/vacancy_parser/models.py` - Pydantic domain models and normalization helpers.
- `src/vacancy_parser/parser/` - source adapters (API/HTML parsers).
- `src/vacancy_parser/storage/` - CSV and PostgreSQL repositories.
- `src/vacancy_parser/analytics/` - salary and skills analytics.
- `src/vacancy_parser/services/pipeline.py` - orchestration layer.
- `src/vacancy_parser/cli.py` - command line interface.
- `tests/` - unit tests for analytics and utils.

## Docker Deploy (recommended)

1. Copy env template:
   - `cp .env.example .env`
2. Set Telegram values in `.env`:
   - `TELEGRAM_BOT_TOKEN=...`
   - `TELEGRAM_CHAT_ID=...`
3. Build and start stack:
   - `docker compose up -d --build`
4. Check scheduler logs:
   - `docker compose logs -f app`
5. Run one-off report:
   - `docker compose run --rm app python -m vacancy_parser.cli report --limit 500`
6. Run one-off alert:
   - `docker compose run --rm app python -m vacancy_parser.cli alert --limit 200`

`app` service starts the daily scheduler automatically (`python -m vacancy_parser.cli scheduler`).
Dashboard moved to a separate project: `../parser_dashboard`.
When running parser as HTTP service (`vacancy_parser.api.main`), it returns raw vacancies only.
Data persistence is handled by `parser_api`.

### Важно про локальный PostgreSQL

Если на Mac уже работает локальный PostgreSQL на `5432`, контейнерная БД пробрасывается на `5433` (`POSTGRES_PORT=5433`).
Тогда локальные команды проекта (`make run-*`) должны использовать `POSTGRES_DSN` с `localhost:5433`.
Внутри Docker-контейнеров используется отдельный DSN `postgres:5432` (настраивается в `docker-compose.yml` автоматически).

## Local Dev (without Docker)

1. Create virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start PostgreSQL:
   - `docker compose up -d postgres`
4. Run parser:
   - `PYTHONPATH=src python -m vacancy_parser.cli parse --query "python backend" --pages 2`
## Makefile Commands

- `make install` - install project dependencies.
- `make postgres-up` - run PostgreSQL in Docker.
- `make run-parse` - parse vacancies with demo query.
- `make run-analyze` - parse and print analytics report.
- `make run-report` - analyze already stored data.
- `make send-alert` - send report summary to Telegram.
- `make run-scheduler` - start daily monitoring and Telegram reports.
- `make compose-up` - build and start Docker stack (`app` + `postgres`).
- `make compose-down` - stop full Docker stack.
- `make compose-logs` - stream scheduler logs from container.
- `make compose-report` - run one-off report inside app container.
- `make compose-alert` - run one-off Telegram alert inside app container.
- `make test` - run tests.
- `make check` - syntax check with `compileall`.

## CLI Commands

- `parse` - collect vacancies and save to CSV + PostgreSQL.
- `analyze` - collect fresh vacancies and then analyze data from DB.
- `report` - analyze already stored vacancies with optional filters.
- `alert` - send report message to Telegram.
- `scheduler` - run daily parser + report sender by schedule from `.env`.

Report includes salary metrics (mean/median/p90), top skills, top companies, and top vacancies.

Scheduler settings are configured by environment variables:
`SCHEDULER_HOUR`, `SCHEDULER_MINUTE`, `SCHEDULER_TIMEZONE`, `SCHEDULER_QUERY`, `SCHEDULER_PAGES`,
`SCHEDULER_LIMIT`, `SCHEDULER_CITY`, `SCHEDULER_EXPERIENCE`, `SCHEDULER_TOP_VACANCIES`.

Database resiliency settings:
`DB_CONNECT_RETRIES`, `DB_CONNECT_RETRY_DELAY_SECONDS`.

## Data Model

- `companies` - unique company directory.
- `vacancies` - vacancy facts and metadata (FK to company).
- `skills` - unique normalized skills.
- `vacancy_skills` - many-to-many relations between vacancies and skills.

## Next Steps

- Add additional vacancy sources.
- Add scheduler (cron or workflow runner).
- Add dashboard (Streamlit).
