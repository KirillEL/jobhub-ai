from typing import Any

from parser_api.db.models import Vacancy
from parser_api.repositories.vacancy_repository import VacancyRepository
from parser_api.schemas.vacancies import (
    CompanyStatResponse,
    SkillStatResponse,
    VacancyInsightsResponse,
    VacancyListFilters,
)


class VacancyService:
    def __init__(self, repository: VacancyRepository) -> None:
        self.repository = repository

    async def list_vacancies(self, filters: VacancyListFilters, user_id: int) -> tuple[list[Vacancy], int]:
        return await self.repository.list(
            user_id=user_id,
            city=filters.city,
            experience=filters.experience,
            search=filters.search,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def get_vacancy(self, external_id: str, user_id: int) -> Vacancy | None:
        return await self.repository.get_by_external_id(external_id=external_id, user_id=user_id)

    async def ingest_vacancies(
        self,
        vacancies: list[dict[str, Any]],
        user_id: int,
        parse_job_id: int | None,
    ) -> int:
        return await self.repository.upsert_many(
            vacancies=vacancies,
            user_id=user_id,
            parse_job_id=parse_job_id,
        )

    async def list_existing_external_ids(self, external_ids: list[str], user_id: int) -> set[str]:
        return await self.repository.list_existing_external_ids(external_ids=external_ids, user_id=user_id)

    async def get_insights(
        self,
        user_id: int,
        city: str | None = None,
        experience: str | None = None,
        search: str | None = None,
        limit: int = 10,
    ) -> VacancyInsightsResponse:
        top_skills = await self.repository.fetch_top_skills(
            user_id=user_id,
            city=city, experience=experience, search=search, limit=limit
        )
        top_companies = await self.repository.fetch_top_companies(
            user_id=user_id,
            city=city, experience=experience, search=search, limit=limit
        )
        return VacancyInsightsResponse(
            top_skills=[SkillStatResponse(skill=skill, count=count) for skill, count in top_skills],
            top_companies=[
                CompanyStatResponse(company=company, count=count)
                for company, count in top_companies
            ],
        )

    async def clear_user_vacancies(self, user_id: int) -> int:
        return await self.repository.delete_user_vacancies(user_id=user_id)
