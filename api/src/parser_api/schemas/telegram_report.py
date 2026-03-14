from pydantic import BaseModel, Field


class TelegramReportSettingsResponse(BaseModel):
    enabled: bool
    telegram_chat_id: str | None
    report_hour: int
    report_minute: int
    report_timezone: str
    report_query: str
    report_pages: int

    class Config:
        from_attributes = True


class TelegramReportSettingsUpdate(BaseModel):
    enabled: bool = False
    telegram_chat_id: str | None = Field(default=None, max_length=64)
    report_hour: int = Field(default=9, ge=0, le=23)
    report_minute: int = Field(default=0, ge=0, le=59)
    report_timezone: str = Field(default="Europe/Moscow", max_length=64)
    report_query: str = Field(default="python backend", min_length=1, max_length=256)
    report_pages: int = Field(default=1, ge=1, le=20)
