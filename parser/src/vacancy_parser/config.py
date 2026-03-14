from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv


class Settings(BaseModel):
    """Настройки только для HTTP-режима парсера (таймаут, без БД и Telegram)."""
    model_config = ConfigDict(frozen=True)

    request_timeout_seconds: int = 20


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
    )
