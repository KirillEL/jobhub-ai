from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from parser_api.api.dependencies import build_parsing_service, get_current_user, get_parsing_service
from parser_api.db.models import ParseJob
from parser_api.db.session import SessionLocal
from parser_api.schemas.parsing import (
    ParseJobListResponse,
    ParseJobStatusResponse,
    ParseRequest,
    ParseResponse,
)
from parser_api.services.parsing_service import ActiveParseJobLimitError, ParsingService

router = APIRouter()


async def _run_parse_job_background(
    job_id: int,
    query: str,
    pages: int,
    user_id: int,
    city: str | None,
    experience: str | None,
    schedule: str | None,
) -> None:
    """Run parse + ingest in a dedicated DB session. Used by BackgroundTasks."""
    db = SessionLocal()
    try:
        service = build_parsing_service(db)
        await service.run_parse_and_ingest(
            job_id=job_id,
            query=query,
            pages=pages,
            user_id=user_id,
            city=city,
            experience=experience,
            schedule=schedule,
        )
    finally:
        await db.close()


@router.post("/jobs", response_model=ParseResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_parsing(
    payload: ParseRequest,
    background_tasks: BackgroundTasks,
    parsing_service: ParsingService = Depends(get_parsing_service),
    current_user=Depends(get_current_user),
) -> ParseResponse:
    try:
        started = await parsing_service.start_parse_job(
            user_id=current_user.id,
            query=payload.query,
            pages=payload.pages,
            idempotency_key=payload.idempotency_key,
        )
    except ActiveParseJobLimitError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    background_tasks.add_task(
        _run_parse_job_background,
        started.job_id,
        payload.query,
        payload.pages,
        current_user.id,
        payload.city,
        payload.experience,
        payload.schedule,
    )
    return ParseResponse(
        status="accepted",
        message="Job queued",
        collected=0,
        job_id=started.job_id,
        new_count=0,
        updated_count=0,
    )


def serialize_job(job: ParseJob) -> ParseJobStatusResponse:
    return ParseJobStatusResponse(
        job_id=job.id,
        query=job.query,
        pages=job.pages,
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        parser_message=job.parser_message,
        error_message=job.error_message,
        collected=job.collected,
        saved_count=job.saved_count,
        new_count=job.new_count,
        updated_count=job.updated_count,
    )


@router.get("/jobs", response_model=ParseJobListResponse, status_code=status.HTTP_200_OK)
async def list_parsing_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    parsing_service: ParsingService = Depends(get_parsing_service),
    current_user=Depends(get_current_user),
) -> ParseJobListResponse:
    jobs = await parsing_service.list_jobs(user_id=current_user.id, limit=limit)
    return ParseJobListResponse(items=[serialize_job(job) for job in jobs])


@router.get("/jobs/{job_id}", response_model=ParseJobStatusResponse, status_code=status.HTTP_200_OK)
async def get_parsing_job(
    job_id: int,
    parsing_service: ParsingService = Depends(get_parsing_service),
    current_user=Depends(get_current_user),
) -> ParseJobStatusResponse:
    job = await parsing_service.get_job_status(job_id=job_id, user_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse job not found")
    return serialize_job(job)
