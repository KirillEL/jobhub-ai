# Job Hub AI

Стек: Postgres, Parser API (FastAPI), HTTP-парсер (HH.ru), опционально — фронт (web).

## Как поднять проект

**1. Создать `.env` в корне репозитория**

```bash
cp .env.example .env
```

Отредактировать при необходимости:
- `POSTGRES_*` — доступ к БД (по умолчанию postgres/postgres/vacancies).
- `CREATE_SCHEMA_ON_START=true` — создать таблицы при первом запуске API.
- Для ежедневного парсинга и отчёта в Telegram: `DAILY_CHECK_ENABLED=true`, задать `DAILY_CHECK_USER_ID` (id пользователя в БД, к которому привязываются вакансии) и `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Если не нужен планировщик — оставить `DAILY_CHECK_ENABLED=false`.

**2. Запустить сервисы**

Из корня репозитория:

```bash
docker compose up -d --build
```

Поднимутся:
- **postgres** — БД (внутренний порт, без проброса на хост по умолчанию).
- **api** — Parser API на порту 8000 (`API_PORT` из `.env`).
- **parser** — HTTP-парсер (внутренний, на 8080).

**3. Проверить**

- API: http://localhost:8000/api/v1/health  
- Документация API: http://localhost:8000/docs  

**4. (Опционально) Фронт**

```bash
cd web
npm install
VITE_API_BASE_URL= npm run dev
```

Открыть http://localhost:5173 (или порт из вывода Vite).

---

Остановить всё: `docker compose down`. Логи: `docker compose logs -f api` (или `parser`, `postgres`).

Подробнее про архитектуру и Telegram: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
