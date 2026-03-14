# Vacancy Parser (HTTP only)

Сервис только с HTTP API: по запросу ходит в HH.ru и возвращает список вакансий. Без БД, без CLI, без планировщика и Telegram.

## Роль

- **POST /parse** — query, pages, city, experience, schedule; заголовок `X-Parser-Token` при включённой авторизации.
- **GET /health** — проверка живости.

Хранение данных и отправка в Telegram выполняются в **parser_api** (см. корневой `docs/ARCHITECTURE.md`).

## Структура

- `src/vacancy_parser/config.py` — настройки (таймаут).
- `src/vacancy_parser/models.py` — модель вакансии (Pydantic).
- `src/vacancy_parser/parser/` — адаптер HH API.
- `src/vacancy_parser/api/main.py` — FastAPI-приложение.

## Запуск

### Docker (рекомендуется)

Из корня репозитория: `docker compose up -d` — парсер поднимается как сервис `parser` из `api/docker-compose.yml`.

Локально только парсер (для разработки):

```bash
cd parser
cp .env.example .env
docker compose up -d --build
# POST http://localhost:8080/parse с телом и заголовком X-Parser-Token
```

### Локально без Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn vacancy_parser.api.main:app --reload --port 8080
```

## Переменные окружения

- `REQUEST_TIMEOUT_SECONDS` — таймаут запросов к HH (по умолчанию 20).
- `PARSER_AUTH_TOKEN` — если задан, запросы к `/parse` требуют заголовок `X-Parser-Token` с этим значением.
