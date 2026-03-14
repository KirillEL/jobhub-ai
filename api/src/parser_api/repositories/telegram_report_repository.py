from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from parser_api.db.models import TelegramReportSettings


class TelegramReportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: int) -> TelegramReportSettings | None:
        stmt = select(TelegramReportSettings).where(TelegramReportSettings.user_id == user_id)
        return await self.db.scalar(stmt)

    async def get_or_create_default(self, user_id: int) -> TelegramReportSettings:
        row = await self.get_by_user_id(user_id)
        if row is not None:
            return row
        row = TelegramReportSettings(
            user_id=user_id,
            enabled=False,
            telegram_chat_id=None,
            report_hour=9,
            report_minute=0,
            report_timezone="Europe/Moscow",
            report_query="python backend",
            report_pages=1,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def upsert(
        self,
        user_id: int,
        *,
        enabled: bool,
        telegram_chat_id: str | None = None,
        report_hour: int = 9,
        report_minute: int = 0,
        report_timezone: str = "Europe/Moscow",
        report_query: str = "python backend",
        report_pages: int = 1,
    ) -> TelegramReportSettings:
        stmt = insert(TelegramReportSettings).values(
            user_id=user_id,
            enabled=enabled,
            telegram_chat_id=telegram_chat_id.strip() or None if telegram_chat_id else None,
            report_hour=report_hour,
            report_minute=report_minute,
            report_timezone=report_timezone,
            report_query=report_query,
            report_pages=report_pages,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[TelegramReportSettings.user_id],
            set_={
                TelegramReportSettings.enabled: stmt.excluded.enabled,
                TelegramReportSettings.telegram_chat_id: stmt.excluded.telegram_chat_id,
                TelegramReportSettings.report_hour: stmt.excluded.report_hour,
                TelegramReportSettings.report_minute: stmt.excluded.report_minute,
                TelegramReportSettings.report_timezone: stmt.excluded.report_timezone,
                TelegramReportSettings.report_query: stmt.excluded.report_query,
                TelegramReportSettings.report_pages: stmt.excluded.report_pages,
            },
        )
        await self.db.execute(stmt)
        await self.db.flush()
        out = await self.get_by_user_id(user_id)
        assert out is not None
        return out

    async def list_enabled_with_chat_id(self) -> list[TelegramReportSettings]:
        stmt = select(TelegramReportSettings).where(
            TelegramReportSettings.enabled.is_(True),
            TelegramReportSettings.telegram_chat_id.isnot(None),
            TelegramReportSettings.telegram_chat_id != "",
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_last_run_at(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(TelegramReportSettings)
            .where(TelegramReportSettings.user_id == user_id)
            .values(last_run_at=now)
        )
        await self.db.execute(stmt)
        await self.db.flush()
