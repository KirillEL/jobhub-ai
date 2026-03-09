# Parser API

Отдельный проект с API на FastAPI для сервиса `vacancy_radar`, построенный по слоистой архитектуре.

## Архитектура проекта

- `api/` - HTTP слой (роуты, зависимости, контракты API).
- `services/` - прикладная бизнес-логика.
- `repositories/` - доступ к данным (асинхронные SQLAlchemy queries).
- `db/` - async engine/session/models.
- `integrations/` - интеграции с внешними сервисами (parser transport).
- `core/` - конфигурация приложения.
- `schemas/` - Pydantic схемы запросов и ответов.
- `alembic/` - миграции БД.

## Ключевые endpoint'ы

- `GET /api/v1/health` - healthcheck API + доступность БД.
- `GET /api/v1/vacancies` - список вакансий с фильтрами `city`, `experience`, `search`, пагинацией `limit/offset`.
- `GET /api/v1/vacancies/{external_id}` - детали вакансии.
- `POST /api/v1/parsing/jobs` - запуск парсинга через интеграционный слой.

## Ежедневная проверка вакансий + Telegram

В API добавлен встроенный планировщик (APScheduler), который может раз в день:

1. Запустить парсер с параметрами из env.
2. Сохранить вакансии в БД.
3. Посчитать, сколько вакансий новых, а сколько обновленных.
4. Отправить отчет в Telegram чат.

### Настройки env

- `DAILY_CHECK_ENABLED=true`
- `DAILY_CHECK_HOUR=9`
- `DAILY_CHECK_MINUTE=0`
- `DAILY_CHECK_TIMEZONE=Europe/Moscow`
- `DAILY_CHECK_QUERY=python backend`
- `DAILY_CHECK_PAGES=1`
- `TELEGRAM_BOT_TOKEN=<bot_token>`
- `TELEGRAM_CHAT_ID=<chat_id>`
- `TELEGRAM_API_BASE_URL=https://api.telegram.org`

Если `DAILY_CHECK_ENABLED=true`, но `TELEGRAM_BOT_TOKEN` или `TELEGRAM_CHAT_ID` не заданы, задача не стартует (будет warning в логах).

## Как API "стучится" в parser

`ParserOrchestrator` использует только HTTP-транспорт:

- API вызывает parser-сервис по HTTP (`parser` контейнер в `docker-compose`).
- Контракт запроса: `POST {PARSER_SERVICE_URL}{PARSER_HTTP_PARSE_PATH}` с JSON:
  `{"query":"python backend","pages":2}`.
- Для защиты internal-endpoint используется заголовок
  `{PARSER_AUTH_HEADER_NAME}: {PARSER_AUTH_TOKEN}` (по умолчанию `X-Parser-Token`).

`parser_api` является единственной точкой записи в БД: parser только возвращает собранные вакансии, а сохранение выполняется внутри API.

### Связка `parser_api` + `parser` в Docker

В `docker-compose.yml` поднимаются оба сервиса:

- `api` - FastAPI (`parser_api`)
- `parser` - HTTP-обертка над parser (`POST /parse`, `GET /health`)

`api` отправляет запросы на `http://parser:8080/parse` внутри docker-сети.
Токен авторизации задается одной переменной `PARSER_AUTH_TOKEN` и передается в оба сервиса.
`parser` не публикует порт на хост (только `expose: 8080`), поэтому извне машины endpoint недоступен.
`postgres` также internal-only в базовом `docker-compose.yml`.

## База данных

Используется PostgreSQL + SQLAlchemy 2.0 в async-режиме (`AsyncSession`).

- DSN задается через `POSTGRES_DSN`.
- Модели соответствуют текущей схеме parser-проекта (`companies`, `vacancies`).
- Изменения схемы делаются через Alembic миграции.

### Alembic (async)

Применить миграции:

- `PYTHONPATH=src alembic upgrade head`

Создать новую миграцию:

- `PYTHONPATH=src alembic revision -m "add new table"`
- `PYTHONPATH=src alembic revision --autogenerate -m "update schema"`

### Makefile команды

- `make install` - установить зависимости.
- `make run-api` - запустить API локально.
- `make check` - проверить синтаксис `src` и `alembic`.
- `make migrate` - применить миграции (`upgrade head`).
- `make migration-new m="message"` - создать пустую миграцию.
- `make migration-autogen m="message"` - создать автоген миграцию.
- `make compose-up` / `make compose-down` - запуск/остановка защищенного docker-стека.
- `make compose-up-debug` / `make compose-down-debug` - запуск/остановка стека с открытым postgres-портом.
- `make compose-logs` / `make compose-logs-debug` - логи сервисов.

## Локальный запуск

1. Создать и активировать виртуальное окружение:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Установить зависимости:
   - `pip install -r requirements.txt`
3. Скопировать env:
   - `cp .env.example .env`
4. Запустить PostgreSQL:
   - `docker compose up -d postgres`
5. Применить миграции:
   - `PYTHONPATH=src alembic upgrade head`
6. Запустить API:
   - `PYTHONPATH=src uvicorn parser_api.main:app --reload --host 0.0.0.0 --port 8000`

Проверка:

- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/health`

## Docker запуск

1. `cp .env.example .env`
2. `docker compose up -d postgres`
3. `docker compose run --rm api sh -c "PYTHONPATH=src alembic upgrade head"`
4. `docker compose up -d --build parser api`
5. `docker compose logs -f api`

### Docker запуск с доступом к PostgreSQL с хоста (debug)

Если нужен доступ к БД с хоста (`localhost:5434`), используй override:

1. `cp .env.example .env`
2. `docker compose -f docker-compose.yml -f docker-compose.local.yml up -d postgres`
3. `docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm api sh -c "PYTHONPATH=src alembic upgrade head"`
4. `docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build parser api`
