from typing import Optional

from pydantic import BaseModel, Field


class VacancyListFilters(BaseModel):
    city: Optional[str] = None
    experience: Optional[str] = None
    search: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class VacancyResponse(BaseModel):
    external_id: str
    title: str
    company: Optional[str] = None
    city: Optional[str] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    currency: Optional[str] = None
    experience: Optional[str] = None
    schedule: Optional[str] = None
    url: str
    published_at: Optional[str] = None


class VacancyListResponse(BaseModel):
    items: list[VacancyResponse]
    total: int
    limit: int
    offset: int


class SkillStatResponse(BaseModel):
    skill: str
    count: int


class CompanyStatResponse(BaseModel):
    company: str
    count: int


class VacancyInsightsResponse(BaseModel):
    top_skills: list[SkillStatResponse]
    top_companies: list[CompanyStatResponse]


class VacancyCleanupResponse(BaseModel):
    removed: int
