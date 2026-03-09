from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from parser_api.db.models import ParseJob


class ParseJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(
        self,
        user_id: int,
        query: str,
        pages: int,
        *,
        status: str = "pending",
        idempotency_key: str | None = None,
    ) -> ParseJob:
        job = ParseJob(
            user_id=user_id,
            query=query,
            pages=pages,
            idempotency_key=idempotency_key,
            status=status,
            started_at=datetime.now(timezone.utc),
            error_message=None,
            parser_message=None,
            collected=None,
            saved_count=None,
            new_count=None,
            updated_count=None,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_job_by_idempotency_key(self, user_id: int, idempotency_key: str) -> ParseJob | None:
        result = await self.db.execute(
            select(ParseJob)
            .where(
                ParseJob.user_id == user_id,
                ParseJob.idempotency_key == idempotency_key,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_job_status(self, job_id: int, status_value: str) -> None:
        await self.db.execute(
            update(ParseJob)
            .where(ParseJob.id == job_id)
            .values(status=status_value, error_message=None)
        )

    async def mark_job_finished(
        self,
        job_id: int,
        status_value: str,
        *,
        error_message: str | None = None,
        parser_message: str | None = None,
        collected: int | None = None,
        saved_count: int | None = None,
        new_count: int | None = None,
        updated_count: int | None = None,
    ) -> None:
        await self.db.execute(
            update(ParseJob)
            .where(ParseJob.id == job_id)
            .values(
                status=status_value,
                finished_at=datetime.now(timezone.utc),
                error_message=error_message,
                parser_message=parser_message,
                collected=collected,
                saved_count=saved_count,
                new_count=new_count,
                updated_count=updated_count,
            )
        )

    async def count_active_jobs_for_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(ParseJob.id).where(
                ParseJob.user_id == user_id,
                ParseJob.status.in_(("pending", "running")),
            )
        )
        return len(result.scalars().all())

    async def fail_stale_running_jobs_for_user(self, user_id: int, stale_after_minutes: int) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(minutes=stale_after_minutes)
        result = await self.db.execute(
            update(ParseJob)
            .where(
                ParseJob.user_id == user_id,
                ParseJob.status == "running",
                ParseJob.started_at < threshold,
                ParseJob.finished_at.is_(None),
            )
            .values(
                status="failed",
                finished_at=datetime.now(timezone.utc),
                error_message="Job timed out while waiting for parser response",
            )
        )
        return int(result.rowcount or 0)

    async def get_job_for_user(self, job_id: int, user_id: int) -> ParseJob | None:
        result = await self.db.execute(
            select(ParseJob).where(ParseJob.id == job_id, ParseJob.user_id == user_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_jobs_for_user(self, user_id: int, limit: int = 10) -> list[ParseJob]:
        result = await self.db.execute(
            select(ParseJob)
            .where(ParseJob.user_id == user_id)
            .order_by(desc(ParseJob.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())
