from __future__ import annotations

import logging
from dataclasses import dataclass

from parser_api.db.models import ParseJob
from parser_api.integrations.parser_client import ParserClientError
from parser_api.repositories.parse_job_repository import ParseJobRepository
from parser_api.services.parser_orchestrator import ParserOrchestrator
from parser_api.services.vacancy_service import VacancyService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsingResult:
    job_id: int
    message: str
    collected: int
    saved: int
    new_count: int
    updated_count: int


@dataclass(frozen=True)
class ParseJobStarted:
    job_id: int


class ActiveParseJobLimitError(RuntimeError):
    pass


class ParsingService:
    def __init__(
        self,
        orchestrator: ParserOrchestrator,
        vacancy_service: VacancyService,
        parse_job_repository: ParseJobRepository,
        max_active_jobs_per_user: int = 1,
        stale_running_timeout_minutes: int = 30,
    ) -> None:
        self.orchestrator = orchestrator
        self.vacancy_service = vacancy_service
        self.parse_job_repository = parse_job_repository
        self.max_active_jobs_per_user = max(1, max_active_jobs_per_user)
        self.stale_running_timeout_minutes = max(1, stale_running_timeout_minutes)

    async def start_parse_job(
        self,
        user_id: int,
        query: str,
        pages: int,
        *,
        idempotency_key: str | None = None,
    ) -> ParseJobStarted:
        """Create a parse job with status 'pending' and return immediately."""
        if idempotency_key:
            existing = await self.parse_job_repository.get_job_by_idempotency_key(
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing:
                return ParseJobStarted(job_id=existing.id)

        stale_failed = await self.parse_job_repository.fail_stale_running_jobs_for_user(
            user_id=user_id,
            stale_after_minutes=self.stale_running_timeout_minutes,
        )
        if stale_failed:
            await self.parse_job_repository.db.commit()
            logger.warning("Marked %s stale running parse jobs as failed for user=%s", stale_failed, user_id)

        active_count = await self.parse_job_repository.count_active_jobs_for_user(user_id=user_id)
        if active_count >= self.max_active_jobs_per_user:
            raise ActiveParseJobLimitError(
                f"Too many active parse jobs: limit is {self.max_active_jobs_per_user}"
            )

        job = await self.parse_job_repository.create_job(
            user_id=user_id,
            query=query,
            pages=pages,
            status="pending",
            idempotency_key=idempotency_key,
        )
        await self.parse_job_repository.db.commit()
        logger.info(
            "Parse job created: job_id=%s user_id=%s query=%s pages=%s",
            job.id,
            user_id,
            query,
            pages,
        )
        return ParseJobStarted(job_id=job.id)

    async def run_parse_and_ingest(
        self,
        job_id: int,
        query: str,
        pages: int,
        user_id: int,
        *,
        city: str | None = None,
        experience: str | None = None,
        schedule: str | None = None,
    ) -> ParsingResult | None:
        """
        Run parser + ingestion in background. Updates job status: pending -> running -> done/failed.
        Uses the service's own DB session; call from a background task with a fresh session.
        Returns ParsingResult on success, None on failure.
        """
        try:
            await self.parse_job_repository.update_job_status(job_id, "running")
            await self.parse_job_repository.db.commit()

            result = await self.orchestrator.trigger_parse(
                query=query,
                pages=pages,
                city=city,
                experience=experience,
                schedule=schedule,
            )
            if result.collected > 0 and not result.vacancies:
                raise ParserClientError("Parser returned no vacancy payload for ingestion")

            external_ids = [str(item.get("external_id", "")).strip() for item in result.vacancies]
            existing_ids = await self.vacancy_service.list_existing_external_ids(
                external_ids, user_id=user_id
            )
            saved = await self.vacancy_service.ingest_vacancies(
                result.vacancies,
                user_id=user_id,
                parse_job_id=job_id,
            )
            unique_external_ids = {item for item in external_ids if item}
            new_count = len(unique_external_ids - existing_ids)
            updated_count = max(0, saved - new_count)
            await self.parse_job_repository.mark_job_finished(
                job_id,
                "done",
                parser_message=result.message[:1000] if result.message else None,
                collected=result.collected,
                saved_count=saved,
                new_count=new_count,
                updated_count=updated_count,
            )
            await self.parse_job_repository.db.commit()
            logger.info(
                "Parse job %s finished: collected=%s saved=%s new=%s updated=%s",
                job_id,
                result.collected,
                saved,
                new_count,
                updated_count,
            )
            return ParsingResult(
                job_id=job_id,
                message=result.message,
                collected=result.collected,
                saved=saved,
                new_count=new_count,
                updated_count=updated_count,
            )
        except Exception as exc:
            logger.exception(
                "Parse job failed: job_id=%s user_id=%s query=%s pages=%s error=%s",
                job_id,
                user_id,
                query,
                pages,
                exc,
            )
            await self.parse_job_repository.mark_job_finished(
                job_id,
                "failed",
                error_message=str(exc)[:1000],
            )
            await self.parse_job_repository.db.commit()
            return None

    async def get_job_status(self, job_id: int, user_id: int) -> ParseJob | None:
        return await self.parse_job_repository.get_job_for_user(job_id=job_id, user_id=user_id)

    async def list_jobs(self, user_id: int, limit: int = 10) -> list[ParseJob]:
        return await self.parse_job_repository.list_jobs_for_user(user_id=user_id, limit=limit)
