from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from parser_api.core.config import get_settings
from parser_api.db.session import get_db
from parser_api.repositories.auth_repository import AuthRepository
from parser_api.repositories.parse_job_repository import ParseJobRepository
from parser_api.repositories.vacancy_repository import VacancyRepository
from parser_api.services.auth_service import AuthService, AuthenticationFailed
from parser_api.services.parser_orchestrator import ParserOrchestrator
from parser_api.services.parsing_service import ParsingService
from parser_api.services.vacancy_service import VacancyService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_vacancy_service(db: AsyncSession = Depends(get_db_session)) -> VacancyService:
    return VacancyService(repository=VacancyRepository(db=db))


def get_parser_orchestrator() -> ParserOrchestrator:
    return ParserOrchestrator(settings=get_settings())


def get_parsing_service(db: AsyncSession = Depends(get_db_session)) -> ParsingService:
    return build_parsing_service(db)


def build_parsing_service(db: AsyncSession) -> ParsingService:
    """Build ParsingService with a given session (e.g. for background tasks)."""
    settings = get_settings()
    vacancy_service = VacancyService(repository=VacancyRepository(db=db))
    orchestrator = ParserOrchestrator(settings=settings)
    parse_job_repository = ParseJobRepository(db=db)
    return ParsingService(
        orchestrator=orchestrator,
        vacancy_service=vacancy_service,
        parse_job_repository=parse_job_repository,
        max_active_jobs_per_user=settings.parse_jobs_max_active_per_user,
        stale_running_timeout_minutes=settings.parse_job_running_timeout_minutes,
    )


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(repository=AuthRepository(db=db), settings=get_settings())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    try:
        return await auth_service.get_user_by_access_token(credentials.credentials)
    except AuthenticationFailed as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
