# Архитектура и Telegram

## Роли сервисов

- **Parser** — только HTTP API: получает запрос (query, pages, city, experience), ходит в HH.ru, возвращает список вакансий. Без БД, без планировщика, без Telegram. Статусный, легко масштабируется по репликам.
- **Parser API** — оркестратор: пользователи, БД (Postgres), вызов парсера по HTTP, сохранение вакансий (в т.ч. привязка к пользователю), планировщик ежедневной проверки, отправка отчётов в Telegram.

## Зачем нужна отправка в Telegram

1. **Ежедневный отчёт** — по расписанию (DAILY_CHECK_*) API запускает парсинг, сохраняет вакансии в общую БД и шлёт в один чат краткий отчёт: сколько собрано, сколько сохранено, новых/обновлённых. Один чат = админ или «системный» пользователь (TELEGRAM_CHAT_ID).
2. **Расширения (по желанию):**
   - Уведомление пользователя по окончании ручного парсинга: если у пользователя в профиле привязан `telegram_chat_id`, после завершения job можно отправить ему результат или ссылку на дашборд.
   - Алерты: при падении парсера/API или ошибках — сообщение в админский чат (тот же TelegramClient в `except` или отдельная джоба).

Вся отправка в Telegram делается **только из Parser API** (один TelegramClient, один бот, конфиг в .env api). Парсер не знает про Telegram.

## Как осуществляется отправка

- В API: `parser_api.integrations.telegram_client.TelegramClient` (async, httpx).
- Вызывается из `DailyCheckScheduler._send_report()` после успешного `run_parse_and_ingest`: формируется текст (время, запрос, collected/saved/new/updated), отправляется в чат `TELEGRAM_CHAT_ID`.
- Параметры: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_API_BASE_URL` (api/.env или корневой .env для docker). Включение ежедневной проверки: `DAILY_CHECK_ENABLED=true`, `DAILY_CHECK_USER_ID` (id пользователя, к которому привязываются вакансии), плюс расписание и запрос (DAILY_CHECK_HOUR, DAILY_CHECK_MINUTE, DAILY_CHECK_QUERY, DAILY_CHECK_PAGES и т.д.).

## Запуск

- Из корня: `docker compose up -d` — поднимаются postgres, api, parser. Планировщик живёт внутри контейнера api; при DAILY_CHECK_ENABLED=true и заданных TELEGRAM_* отчёты уходят в Telegram по расписанию.
