from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Parser API"
    app_description: str = "API service for vacancy parser data"
    app_version: str = "0.2.0"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins_raw: str = "http://localhost:3000,http://localhost:5173"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    auth_cookie_name: str = "refresh_token"
    auth_cookie_secure: bool = False
    auth_cookie_domain: str | None = None
    auth_cookie_samesite: str = "lax"

    postgres_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vacancies"
    create_schema_on_start: bool = False

    parser_service_url: str = "http://parser:8080"
    parser_http_parse_path: str = "/parse"
    parser_http_timeout_seconds: int = 120
    parser_http_retries: int = 2
    parser_http_retry_backoff_seconds: float = 1.5
    parser_auth_header_name: str = "X-Parser-Token"
    parser_auth_token: str | None = None
    parse_jobs_max_active_per_user: int = 1
    parse_job_running_timeout_minutes: int = 30
    daily_check_enabled: bool = False
    daily_check_user_id: int | None = None  # User to attach daily check jobs and vacancies to
    daily_check_hour: int = 9
    daily_check_minute: int = 0
    daily_check_timezone: str = "Europe/Moscow"
    daily_check_query: str = "python backend"
    daily_check_pages: int = 1
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_api_base_url: str = "https://api.telegram.org"

    @property
    def cors_allow_origins(self) -> list[str]:
        raw = self.cors_allow_origins_raw.strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
