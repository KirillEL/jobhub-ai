import os

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from vacancy_parser.config import get_settings
from vacancy_parser.models import Vacancy
from vacancy_parser.parser.hh_api import HeadHunterApiProvider

app = FastAPI(title="Vacancy Parser API", version="0.1.0")
PARSER_AUTH_TOKEN = os.getenv("PARSER_AUTH_TOKEN")


class ParseRequest(BaseModel):
    query: str = Field(min_length=2, max_length=256)
    pages: int = Field(default=1, ge=1, le=20)
    city: str | None = Field(default=None, max_length=120)
    experience: str | None = Field(default=None, max_length=120)
    schedule: str | None = Field(default=None, max_length=120)


class ParseResponse(BaseModel):
    status: str
    message: str
    collected: int
    vacancies: list[Vacancy]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse(payload: ParseRequest, x_parser_token: str | None = Header(default=None)) -> ParseResponse:
    if PARSER_AUTH_TOKEN and x_parser_token != PARSER_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid parser token",
        )
    settings = get_settings()
    provider = HeadHunterApiProvider(timeout_seconds=settings.request_timeout_seconds)
    vacancies = provider.fetch(
        query=payload.query,
        pages=payload.pages,
        city=payload.city,
        experience=payload.experience,
        schedule=payload.schedule,
    )
    return ParseResponse(
        status="ok",
        message="Parsing completed, data is ready for ingestion",
        collected=len(vacancies),
        vacancies=vacancies,
    )
