from fastapi import APIRouter, Depends, status

from parser_api.api.dependencies import get_current_user
from parser_api.db.models import User
from parser_api.db.session import SessionLocal
from parser_api.repositories.telegram_report_repository import TelegramReportRepository
from parser_api.schemas.telegram_report import (
    TelegramReportSettingsResponse,
    TelegramReportSettingsUpdate,
)

router = APIRouter()


@router.get("/telegram-report", response_model=TelegramReportSettingsResponse)
async def get_telegram_report_settings(
    current_user: User = Depends(get_current_user),
):
    async with SessionLocal() as db:
        repo = TelegramReportRepository(db=db)
        row = await repo.get_or_create_default(user_id=current_user.id)
        await db.commit()
        return TelegramReportSettingsResponse(
            enabled=row.enabled,
            telegram_chat_id=row.telegram_chat_id,
            report_hour=row.report_hour,
            report_minute=row.report_minute,
            report_timezone=row.report_timezone,
            report_query=row.report_query,
            report_pages=row.report_pages,
        )


@router.put("/telegram-report", response_model=TelegramReportSettingsResponse)
async def update_telegram_report_settings(
    payload: TelegramReportSettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    async with SessionLocal() as db:
        repo = TelegramReportRepository(db=db)
        row = await repo.upsert(
            user_id=current_user.id,
            enabled=payload.enabled,
            telegram_chat_id=payload.telegram_chat_id,
            report_hour=payload.report_hour,
            report_minute=payload.report_minute,
            report_timezone=payload.report_timezone,
            report_query=payload.report_query,
            report_pages=payload.report_pages,
        )
        await db.commit()
        return TelegramReportSettingsResponse(
            enabled=row.enabled,
            telegram_chat_id=row.telegram_chat_id,
            report_hour=row.report_hour,
            report_minute=row.report_minute,
            report_timezone=row.report_timezone,
            report_query=row.report_query,
            report_pages=row.report_pages,
        )
