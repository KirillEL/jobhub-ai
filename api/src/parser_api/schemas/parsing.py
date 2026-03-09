from datetime import datetime

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    query: str = Field(min_length=2, max_length=256)
    pages: int = Field(default=1, ge=1, le=20)
    city: str | None = Field(default=None, max_length=120)
    experience: str | None = Field(default=None, max_length=120)
    schedule: str | None = Field(default=None, max_length=120)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ParseResponse(BaseModel):
    status: str
    message: str
    collected: int
    job_id: int
    new_count: int
    updated_count: int


class ParseJobStatusResponse(BaseModel):
    job_id: int
    query: str
    pages: int
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    parser_message: str | None = None
    error_message: str | None = None
    collected: int | None = None
    saved_count: int | None = None
    new_count: int | None = None
    updated_count: int | None = None


class ParseJobListResponse(BaseModel):
    items: list[ParseJobStatusResponse]
