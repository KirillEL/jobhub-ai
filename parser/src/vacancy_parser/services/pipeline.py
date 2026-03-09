from __future__ import annotations

from pydantic import BaseModel
from vacancy_parser.analytics.metrics import salary_summary
from vacancy_parser.models import Vacancy
from vacancy_parser.parser.base import VacancyProvider
from vacancy_parser.storage.csv_repository import CsvVacancyRepository
from vacancy_parser.storage.postgresql_repository import PostgresVacancyRepository


class PipelineResult(BaseModel):
    vacancies: list[Vacancy]
    summary: dict[str, float | int | None]
    skills: list[tuple[str, int]]
    companies: list[tuple[str, int]]


class VacancyPipeline:
    def __init__(
        self,
        provider: VacancyProvider,
        csv_repository: CsvVacancyRepository,
        postgres_repository: PostgresVacancyRepository,
    ) -> None:
        self.provider = provider
        self.csv_repository = csv_repository
        self.postgres_repository = postgres_repository

    def collect(self, query: str, pages: int) -> list[Vacancy]:
        vacancies = self.provider.fetch(query=query, pages=pages)
        self.csv_repository.save(vacancies)
        self.postgres_repository.init_schema()
        self.postgres_repository.upsert_many(vacancies)
        return vacancies

    def analyze(self, vacancies: list[Vacancy]) -> PipelineResult:
        return PipelineResult(
            vacancies=vacancies,
            summary=salary_summary(vacancies),
            skills=self.postgres_repository.fetch_top_skills(limit=10),
            companies=self.postgres_repository.fetch_top_companies(limit=5),
        )

    def analyze_from_storage(
        self,
        city: str | None = None,
        experience: str | None = None,
        limit: int = 1000,
    ) -> PipelineResult:
        self.postgres_repository.init_schema()
        vacancies = self.postgres_repository.fetch_vacancies(
            city=city,
            experience=experience,
            limit=limit,
        )
        skills = self.postgres_repository.fetch_top_skills(
            limit=10,
            city=city,
            experience=experience,
        )
        companies = self.postgres_repository.fetch_top_companies(
            limit=5,
            city=city,
            experience=experience,
        )
        return PipelineResult(
            vacancies=vacancies,
            summary=salary_summary(vacancies),
            skills=skills,
            companies=companies,
        )

