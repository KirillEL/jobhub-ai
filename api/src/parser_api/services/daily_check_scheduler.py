from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from parser_api.api.dependencies import build_parsing_service
from parser_api.core.config import Settings, get_settings
from parser_api.db.session import SessionLocal
from parser_api.integrations.parser_client import ParserClientError
from parser_api.integrations.telegram_client import TelegramClient, TelegramClientError
from parser_api.repositories.telegram_report_repository import TelegramReportRepository
from parser_api.repositories.vacancy_repository import VacancyRepository
from parser_api.services.parsing_service import ParsingResult

logger = logging.getLogger(__name__)


def _resolve_timezone(tz_name: str) -> timezone | ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        logger.warning("Invalid timezone %s, fallback to UTC", tz_name)
        return timezone.utc


class DailyCheckScheduler:
    """Запускает ежедневные отчёты по настройкам из БД (telegram_report_settings)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler: AsyncIOScheduler | None = None

    def start(self) -> None:
        if not self.settings.telegram_bot_token:
            logger.info("TELEGRAM_BOT_TOKEN not set; daily report scheduler disabled")
            return
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self.scheduler.add_job(
            self._tick,
            trigger=CronTrigger(minute="*"),  # every minute
            id="daily_report_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        logger.info("Daily report scheduler started (checks every minute)")

    def shutdown(self) -> None:
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None

    async def _tick(self) -> None:
        """Раз в минуту: проверить, кому пора отправить отчёт, и отправить."""
        settings = get_settings()
        if not settings.telegram_bot_token:
            return
        async with SessionLocal() as db:
            repo = TelegramReportRepository(db=db)
            rows = await repo.list_enabled_with_chat_id()
            await db.commit()

        for row in rows:
            tz = _resolve_timezone(row.report_timezone)
            now_in_tz = datetime.now(tz)
            if now_in_tz.hour != row.report_hour or now_in_tz.minute != row.report_minute:
                continue
            if row.last_run_at is not None:
                last_in_tz = row.last_run_at.astimezone(tz)
                if last_in_tz.date() >= now_in_tz.date():
                    continue
            await self._run_report_for_user(
                user_id=row.user_id,
                chat_id=row.telegram_chat_id or "",
                query=row.report_query,
                pages=row.report_pages,
            )

    async def _run_report_for_user(
        self,
        user_id: int,
        chat_id: str,
        query: str,
        pages: int,
    ) -> None:
        try:
            async with SessionLocal() as db:
                parsing_service = build_parsing_service(db)
                started = await parsing_service.start_parse_job(
                    user_id=user_id,
                    query=query,
                    pages=pages,
                )
                result: ParsingResult | None = await parsing_service.run_parse_and_ingest(
                    job_id=started.job_id,
                    query=query,
                    pages=pages,
                    user_id=user_id,
                )
            if result is not None:
                client = TelegramClient(
                    api_base_url=self.settings.telegram_api_base_url,
                    bot_token=self.settings.telegram_bot_token or "",
                    chat_id=chat_id,
                )
                text = await self._build_report_text(
                    query=query,
                    result=result,
                    user_id=user_id,
                    job_id=started.job_id,
                )
                await client.send_message(text=text)
                async with SessionLocal() as db:
                    repo = TelegramReportRepository(db=db)
                    await repo.set_last_run_at(user_id)
                    await db.commit()
                logger.info(
                    "Daily report sent for user_id=%s: collected=%s saved=%s",
                    user_id,
                    result.collected,
                    result.saved,
                )
            else:
                logger.warning("Daily report run failed for user_id=%s", user_id)
        except (ParserClientError, TelegramClientError, ValueError) as exc:
            logger.exception("Daily report failed for user_id=%s: %s", user_id, exc)
        except Exception:
            logger.exception("Daily report failed for user_id=%s with unexpected error", user_id)

    async def _build_report_text(
        self,
        query: str,
        result: ParsingResult,
        user_id: int,
        job_id: int,
    ) -> str:
        """Формирует текст отчёта: акцент на новых (уникальных) вакансиях и ссылки на них."""
        new_count = result.new_count
        updated_count = result.updated_count
        collected = result.collected

        lines: list[str] = []
        if new_count > 0:
            lines.append(
                f"🆕 <b>Появилось {new_count} новых вакансий</b> по запросу «<code>{query}</code>»."
            )
        else:
            lines.append(
                f"По запросу «<code>{query}</code>» новых вакансий не появилось. "
                f"Проверено: {collected}."
            )
        if updated_count > 0:
            lines.append(f"Обновлено: {updated_count}.")
        lines.append("")

        links: list[tuple[str, str]] = []
        try:
            async with SessionLocal() as db:
                repo = VacancyRepository(db=db)
                links = await repo.list_titles_urls_by_parse_job(
                    user_id=user_id, parse_job_id=job_id, limit=5
                )
        except Exception:
            pass

        if new_count > 0 and links:
            lines.append("<b>Новые вакансии:</b>")
            for title, url in links:
                title_esc = (title or "Без названия").replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f"• <a href=\"{url}\">{title_esc}</a>")

        return "\n".join(lines).strip()
