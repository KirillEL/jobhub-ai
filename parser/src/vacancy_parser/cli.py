from __future__ import annotations

import argparse

from vacancy_parser.config import get_settings
from vacancy_parser.notifications.telegram import TelegramNotifier
from vacancy_parser.parser.hh_api import HeadHunterApiProvider
from vacancy_parser.services.alerts import build_report_text
from vacancy_parser.services.pipeline import VacancyPipeline
from vacancy_parser.services.scheduler import run_daily_scheduler
from vacancy_parser.storage.csv_repository import CsvVacancyRepository
from vacancy_parser.storage.postgresql_repository import PostgresVacancyRepository


def build_pipeline() -> VacancyPipeline:
    settings = get_settings()
    provider = HeadHunterApiProvider(timeout_seconds=settings.request_timeout_seconds)
    csv_repository = CsvVacancyRepository(settings.csv_path)
    postgres_repository = PostgresVacancyRepository(
        dsn=settings.postgres_dsn,
        connect_retries=settings.db_connect_retries,
        retry_delay_seconds=settings.db_connect_retry_delay_seconds,
    )
    return VacancyPipeline(
        provider=provider,
        csv_repository=csv_repository,
        postgres_repository=postgres_repository,
    )


def cmd_parse(query: str, pages: int) -> None:
    pipeline = build_pipeline()
    vacancies = pipeline.collect(query=query, pages=pages)
    print(f"Собрано вакансий: {len(vacancies)}")


def cmd_analyze(query: str, pages: int) -> None:
    pipeline = build_pipeline()
    pipeline.collect(query=query, pages=pages)
    report = pipeline.analyze_from_storage()
    print(build_report_text(report=report, top_vacancies=5, city=None, experience=None))


def cmd_report(city: str | None, experience: str | None, limit: int) -> None:
    pipeline = build_pipeline()
    report = pipeline.analyze_from_storage(city=city, experience=experience, limit=limit)
    print(build_report_text(report=report, top_vacancies=5, city=city, experience=experience))


def cmd_alert(
    city: str | None,
    experience: str | None,
    limit: int,
    parse_first: bool,
    query: str | None,
    pages: int,
    top_vacancies: int,
) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise ValueError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    pipeline = build_pipeline()
    if parse_first:
        if not query:
            raise ValueError("--query is required when --parse-first is set")
        pipeline.collect(query=query, pages=pages)

    report = pipeline.analyze_from_storage(city=city, experience=experience, limit=limit)
    message = build_report_text(
        report=report,
        top_vacancies=top_vacancies,
        with_emoji=True,
        city=city,
        experience=experience,
    )
    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        timeout_seconds=settings.request_timeout_seconds,
    )
    notifier.send_message(message)
    print("Отчет отправлен в Telegram.")


def cmd_scheduler(run_now: bool) -> None:
    settings = get_settings()
    pipeline = build_pipeline()
    run_daily_scheduler(pipeline=pipeline, settings=settings, run_now=run_now)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vacancy parser CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="Collect vacancies")
    parse_cmd.add_argument("--query", required=True, help="Search query")
    parse_cmd.add_argument("--pages", type=int, default=1, help="Pages to parse")

    analyze_cmd = subparsers.add_parser("analyze", help="Collect and analyze vacancies")
    analyze_cmd.add_argument("--query", required=True, help="Search query")
    analyze_cmd.add_argument("--pages", type=int, default=1, help="Pages to parse")

    report_cmd = subparsers.add_parser("report", help="Analyze vacancies already stored in PostgreSQL")
    report_cmd.add_argument("--city", help="Filter by city", default=None)
    report_cmd.add_argument("--experience", help="Filter by experience", default=None)
    report_cmd.add_argument("--limit", type=int, default=1000, help="Maximum rows from DB")

    alert_cmd = subparsers.add_parser("alert", help="Send report to Telegram")
    alert_cmd.add_argument("--city", help="Filter by city", default=None)
    alert_cmd.add_argument("--experience", help="Filter by experience", default=None)
    alert_cmd.add_argument("--limit", type=int, default=200, help="Maximum rows from DB")
    alert_cmd.add_argument(
        "--parse-first",
        action="store_true",
        help="Collect fresh vacancies before sending alert",
    )
    alert_cmd.add_argument("--query", help="Search query for --parse-first", default=None)
    alert_cmd.add_argument("--pages", type=int, default=1, help="Pages to parse with --parse-first")
    alert_cmd.add_argument("--top-vacancies", type=int, default=5, help="How many links to include")

    scheduler_cmd = subparsers.add_parser("scheduler", help="Run daily Telegram monitoring")
    scheduler_cmd.add_argument(
        "--run-now",
        action="store_true",
        help="Run one report immediately after scheduler start",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "parse":
        cmd_parse(query=args.query, pages=args.pages)
    elif args.command == "analyze":
        cmd_analyze(query=args.query, pages=args.pages)
    elif args.command == "report":
        cmd_report(city=args.city, experience=args.experience, limit=args.limit)
    elif args.command == "alert":
        cmd_alert(
            city=args.city,
            experience=args.experience,
            limit=args.limit,
            parse_first=args.parse_first,
            query=args.query,
            pages=args.pages,
            top_vacancies=args.top_vacancies,
        )
    elif args.command == "scheduler":
        cmd_scheduler(run_now=args.run_now)


if __name__ == "__main__":
    main()

