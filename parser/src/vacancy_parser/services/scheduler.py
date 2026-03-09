from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from vacancy_parser.config import Settings
from vacancy_parser.notifications.telegram import TelegramNotifier
from vacancy_parser.services.alerts import build_report_text
from vacancy_parser.services.pipeline import VacancyPipeline


def _build_scheduler_start_text(settings: Settings, now: datetime) -> str:
    return (
        "🟢 Плановый запуск парсинга стартовал.\n"
        f"Время: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Запрос: {settings.scheduler_query}\n"
        f"Страниц: {settings.scheduler_pages}\n"
        f"Фильтры: город={settings.scheduler_city or 'любой'}, "
        f"опыт={settings.scheduler_experience or 'любой'}"
    )


def _build_scheduler_success_text(now: datetime, vacancies_count: int) -> str:
    return (
        "✅ Плановый запуск завершен успешно.\n"
        f"Время завершения: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Обработано вакансий в отчете: {vacancies_count}"
    )


def _build_scheduler_error_text(now: datetime, error: Exception) -> str:
    error_name = error.__class__.__name__
    error_text = str(error).strip() or "без описания"
    short_error = error_text[:300]
    return (
        "🔴 Ошибка во время планового запуска.\n"
        f"Время: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Тип: {error_name}\n"
        f"Причина: {short_error}"
    )


def send_daily_report(pipeline: VacancyPipeline, settings: Settings) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise ValueError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    timezone = ZoneInfo(settings.scheduler_timezone)
    started_at = datetime.now(timezone)
    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        timeout_seconds=settings.request_timeout_seconds,
    )
    notifier.send_message(_build_scheduler_start_text(settings=settings, now=started_at))
    try:
        pipeline.collect(query=settings.scheduler_query, pages=settings.scheduler_pages)
        report = pipeline.analyze_from_storage(
            city=settings.scheduler_city,
            experience=settings.scheduler_experience,
            limit=settings.scheduler_limit,
        )
        report_message = build_report_text(
            report=report,
            top_vacancies=settings.scheduler_top_vacancies,
            with_emoji=True,
            city=settings.scheduler_city,
            experience=settings.scheduler_experience,
        )
        notifier.send_message(report_message)
        finished_at = datetime.now(timezone)
        notifier.send_message(
            _build_scheduler_success_text(
                now=finished_at,
                vacancies_count=len(report.vacancies),
            )
        )
    except Exception as exc:
        failed_at = datetime.now(timezone)
        notifier.send_message(_build_scheduler_error_text(now=failed_at, error=exc))
        raise


def run_daily_scheduler(
    pipeline: VacancyPipeline,
    settings: Settings,
    run_now: bool = False,
) -> None:
    timezone = ZoneInfo(settings.scheduler_timezone)
    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        send_daily_report,
        trigger="cron",
        hour=settings.scheduler_hour,
        minute=settings.scheduler_minute,
        kwargs={"pipeline": pipeline, "settings": settings},
        id="daily-telegram-report",
        replace_existing=True,
    )

    print(
        "Планировщик запущен. Ежедневная отправка в "
        f"{settings.scheduler_hour:02d}:{settings.scheduler_minute:02d} ({settings.scheduler_timezone})."
    )
    if run_now:
        print("Выполняю пробную отправку сразу...")
        send_daily_report(pipeline=pipeline, settings=settings)
        print("Пробная отправка завершена.")
    print("Остановить: Ctrl+C")
    scheduler.start()

