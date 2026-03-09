from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from parser_api.api.dependencies import build_parsing_service
from parser_api.core.config import Settings
from parser_api.db.session import SessionLocal
from parser_api.integrations.parser_client import ParserClientError
from parser_api.integrations.telegram_client import TelegramClient, TelegramClientError
from parser_api.services.parsing_service import ParsingResult

logger = logging.getLogger(__name__)


class DailyCheckScheduler:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler: AsyncIOScheduler | None = None
        self.telegram_client: TelegramClient | None = None

        if settings.telegram_bot_token and settings.telegram_chat_id:
            self.telegram_client = TelegramClient(
                api_base_url=settings.telegram_api_base_url,
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
            )

    def start(self) -> None:
        if not self.settings.daily_check_enabled:
            logger.info("Daily vacancy check is disabled")
            return
        if self.settings.daily_check_user_id is None:
            logger.warning(
                "Daily vacancy check is enabled but DAILY_CHECK_USER_ID is not set; scheduler not started"
            )
            return
        if not self.telegram_client:
            logger.warning(
                "Daily vacancy check is enabled but Telegram credentials are missing; scheduler not started"
            )
            return

        timezone_value = self._resolve_timezone()
        trigger = CronTrigger(
            hour=self.settings.daily_check_hour,
            minute=self.settings.daily_check_minute,
            timezone=timezone_value,
        )
        self.scheduler = AsyncIOScheduler(timezone=timezone_value)
        self.scheduler.add_job(
            self.run_check_once,
            trigger=trigger,
            id="daily_vacancy_check",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        logger.info(
            "Daily vacancy check scheduled at %02d:%02d (%s)",
            self.settings.daily_check_hour,
            self.settings.daily_check_minute,
            self.settings.daily_check_timezone,
        )

    def shutdown(self) -> None:
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None

    async def run_check_once(self) -> None:
        logger.info("Daily vacancy check started")
        user_id = self.settings.daily_check_user_id
        if user_id is None:
            return
        try:
            async with SessionLocal() as db:
                parsing_service = build_parsing_service(db)
                started = await parsing_service.start_parse_job(
                    user_id=user_id,
                    query=self.settings.daily_check_query,
                    pages=self.settings.daily_check_pages,
                )
                result: ParsingResult | None = await parsing_service.run_parse_and_ingest(
                    job_id=started.job_id,
                    query=self.settings.daily_check_query,
                    pages=self.settings.daily_check_pages,
                    user_id=user_id,
                )
            if result is not None:
                await self._send_report(result)
                logger.info(
                    "Daily vacancy check completed: collected=%s saved=%s new=%s updated=%s",
                    result.collected,
                    result.saved,
                    result.new_count,
                    result.updated_count,
                )
            else:
                logger.warning("Daily vacancy check finished with failure (see above)")
        except (ParserClientError, TelegramClientError, ValueError) as exc:
            logger.exception("Daily vacancy check failed: %s", exc)
        except Exception:
            logger.exception("Daily vacancy check failed with unexpected error")

    async def _send_report(self, result: ParsingResult) -> None:
        if not self.telegram_client:
            return
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        text = (
            "✅ <b>Ежедневная проверка вакансий</b>\n"
            f"Время: <code>{now}</code>\n"
            f"Запрос: <code>{self.settings.daily_check_query}</code>\n"
            f"Страниц: <code>{self.settings.daily_check_pages}</code>\n\n"
            f"Получено: <b>{result.collected}</b>\n"
            f"Сохранено: <b>{result.saved}</b>\n"
            f"Новых: <b>{result.new_count}</b>\n"
            f"Обновлено: <b>{result.updated_count}</b>\n\n"
            f"Сообщение парсера: {result.message}"
        )
        await self.telegram_client.send_message(text=text)

    def _resolve_timezone(self) -> timezone | ZoneInfo:
        try:
            return ZoneInfo(self.settings.daily_check_timezone)
        except ZoneInfoNotFoundError:
            logger.warning(
                "Invalid DAILY_CHECK_TIMEZONE=%s, fallback to UTC",
                self.settings.daily_check_timezone,
            )
            return timezone.utc
