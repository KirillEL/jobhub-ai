from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from parser_api.api.dependencies import get_db_session
from parser_api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def healthcheck(db: AsyncSession = Depends(get_db_session)) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError:
        database = "error"
    return HealthResponse(status="ok", database=database)
