from fastapi import APIRouter

from parser_api.api.v1.endpoints.auth import router as auth_router
from parser_api.api.v1.endpoints.health import router as health_router
from parser_api.api.v1.endpoints.parsing import router as parsing_router
from parser_api.api.v1.endpoints.vacancies import router as vacancies_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(vacancies_router, prefix="/vacancies", tags=["vacancies"])
api_router.include_router(parsing_router, prefix="/parsing", tags=["parsing"])
