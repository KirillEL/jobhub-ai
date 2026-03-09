from __future__ import annotations

from vacancy_parser.services.pipeline import PipelineResult


def _format_money(value: float | int | None) -> str:
    if value is None:
        return "нет данных"
    return f"{value:,.0f}".replace(",", " ")


def _format_filter_value(value: str | None) -> str:
    return value if value else "любой"


def build_report_text(
    report: PipelineResult,
    top_vacancies: int = 5,
    with_emoji: bool = False,
    city: str | None = None,
    experience: str | None = None,
) -> str:
    summary = report.summary
    prefix = "📊 " if with_emoji else ""
    bullet = "•" if with_emoji else "-"
    skill_icon = "🧠 " if with_emoji else ""
    vacancy_icon = "💼 " if with_emoji else ""

    lines = [
        f"{prefix}Отчет по вакансиям",
        "",
        f"Всего вакансий: {summary.get('count')}",
        f"Город: {_format_filter_value(city)}",
        f"Опыт: {_format_filter_value(experience)}",
        f"С указанием зарплаты: {summary.get('salary_count')}",
        f"Средняя зарплата: {_format_money(summary.get('mean'))}",
        f"Медианная зарплата: {_format_money(summary.get('median'))}",
        f"P90 зарплаты: {_format_money(summary.get('p90'))}",
        "",
        "🏢 Топ компаний:" if with_emoji else "Топ компаний:",
    ]
    if report.companies:
        for company, count in report.companies[:5]:
            lines.append(f"{bullet} {company}: {count}")
    else:
        lines.append(f"{bullet} Компании не найдены")

    lines += [
        "",
        f"{skill_icon}Топ навыков:",
    ]
    if report.skills:
        for skill, count in report.skills[:10]:
            lines.append(f"{bullet} {skill}: {count}")
    else:
        lines.append(f"{bullet} Навыки не найдены")

    lines.append("")
    lines.append(f"{vacancy_icon}Топ вакансий:")
    if report.vacancies:
        for vacancy in report.vacancies[:top_vacancies]:
            lines.append(f"{bullet} {vacancy.title} — {vacancy.company}")
            lines.append(f"  {vacancy.url}")
    else:
        lines.append(f"{bullet} По выбранным фильтрам вакансий нет")

    return "\n".join(lines)


def build_telegram_alert_text(report: PipelineResult, top_vacancies: int = 5) -> str:
    return build_report_text(report=report, top_vacancies=top_vacancies, with_emoji=True)

