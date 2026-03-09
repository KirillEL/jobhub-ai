from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_timeout_seconds: int = 20
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/vacancies"
    postgres_dsn_internal: str | None = None
    csv_path: Path = Path("data/raw/vacancies.csv")
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    scheduler_hour: int = 9
    scheduler_minute: int = 0
    scheduler_timezone: str = "Europe/Moscow"
    scheduler_query: str = "python backend"
    scheduler_pages: int = 2
    scheduler_limit: int = 300
    scheduler_city: str | None = None
    scheduler_experience: str | None = None
    scheduler_top_vacancies: int = 5
    db_connect_retries: int = 10
    db_connect_retry_delay_seconds: float = 2.0


def get_settings() -> Settings:
    # Load .env from project root (if present) before reading env vars.
    load_dotenv()
    external_dsn = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/vacancies")
    internal_dsn = os.getenv("POSTGRES_DSN_INTERNAL")
    return Settings(
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
        postgres_dsn=internal_dsn or external_dsn,
        postgres_dsn_internal=internal_dsn,
        csv_path=Path(os.getenv("VACANCY_CSV_PATH", "data/raw/vacancies.csv")),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        scheduler_hour=int(os.getenv("SCHEDULER_HOUR", "9")),
        scheduler_minute=int(os.getenv("SCHEDULER_MINUTE", "0")),
        scheduler_timezone=os.getenv("SCHEDULER_TIMEZONE", "Europe/Moscow"),
        scheduler_query=os.getenv("SCHEDULER_QUERY", "python backend"),
        scheduler_pages=int(os.getenv("SCHEDULER_PAGES", "2")),
        scheduler_limit=int(os.getenv("SCHEDULER_LIMIT", "300")),
        scheduler_city=os.getenv("SCHEDULER_CITY") or None,
        scheduler_experience=os.getenv("SCHEDULER_EXPERIENCE") or None,
        scheduler_top_vacancies=int(os.getenv("SCHEDULER_TOP_VACANCIES", "5")),
        db_connect_retries=int(os.getenv("DB_CONNECT_RETRIES", "10")),
        db_connect_retry_delay_seconds=float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2.0")),
    )

