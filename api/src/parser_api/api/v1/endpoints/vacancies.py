from fastapi import APIRouter, Depends, HTTPException, Query, status

from parser_api.api.dependencies import get_current_user, get_vacancy_service
from parser_api.db.models import Vacancy
from parser_api.schemas.vacancies import (
    VacancyCleanupResponse,
    VacancyInsightsResponse,
    VacancyListFilters,
    VacancyListResponse,
    VacancyResponse,
)
from parser_api.services.vacancy_service import VacancyService

router = APIRouter()


def _map_vacancy(vacancy: Vacancy) -> VacancyResponse:
    company_name = vacancy.company_rel.name if vacancy.company_rel else vacancy.company
    return VacancyResponse(
        external_id=vacancy.external_id,
        title=vacancy.title,
        company=company_name,
        city=vacancy.city,
        salary_from=vacancy.salary_from,
        salary_to=vacancy.salary_to,
        currency=vacancy.currency,
        experience=vacancy.experience,
        schedule=vacancy.schedule,
        url=vacancy.url,
        published_at=vacancy.published_at,
    )


@router.get("", response_model=VacancyListResponse)
async def list_vacancies(
    city: str | None = Query(default=None),
    experience: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: VacancyService = Depends(get_vacancy_service),
    current_user=Depends(get_current_user),
) -> VacancyListResponse:
    filters = VacancyListFilters(
        city=city,
        experience=experience,
        search=search,
        limit=limit,
        offset=offset,
    )
    vacancies, total = await service.list_vacancies(filters=filters, user_id=current_user.id)
    return VacancyListResponse(
        items=[_map_vacancy(item) for item in vacancies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/insights", response_model=VacancyInsightsResponse)
async def vacancy_insights(
    city: str | None = Query(default=None),
    experience: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=30),
    service: VacancyService = Depends(get_vacancy_service),
    current_user=Depends(get_current_user),
) -> VacancyInsightsResponse:
    return await service.get_insights(
        user_id=current_user.id,
        city=city,
        experience=experience,
        search=search,
        limit=limit,
    )


@router.get("/{external_id}", response_model=VacancyResponse)
async def get_vacancy(
    external_id: str,
    service: VacancyService = Depends(get_vacancy_service),
    current_user=Depends(get_current_user),
) -> VacancyResponse:
    vacancy = await service.get_vacancy(external_id=external_id, user_id=current_user.id)
    if vacancy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found"
        )
    return _map_vacancy(vacancy)


@router.delete("/my", response_model=VacancyCleanupResponse)
async def clear_my_vacancies(
    service: VacancyService = Depends(get_vacancy_service),
    current_user=Depends(get_current_user),
) -> VacancyCleanupResponse:
    removed = await service.clear_user_vacancies(user_id=current_user.id)
    return VacancyCleanupResponse(removed=removed)
