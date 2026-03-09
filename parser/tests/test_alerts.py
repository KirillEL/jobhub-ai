from vacancy_parser.models import Vacancy
from vacancy_parser.services.alerts import build_telegram_alert_text
from vacancy_parser.services.pipeline import PipelineResult


def test_build_telegram_alert_text_contains_main_sections() -> None:
    report = PipelineResult(
        vacancies=[
            Vacancy(
                external_id="1",
                title="Python Developer",
                company="Acme",
                city="Moscow",
                salary_from=200000,
                salary_to=300000,
                currency="RUR",
                experience="1-3 years",
                schedule="Remote",
                url="https://example.com/v/1",
                published_at=None,
                description="Python SQL",
            )
        ],
        summary={"count": 1, "salary_count": 1, "mean": 250000.0, "median": 250000.0},
        skills=[("python", 1), ("sql", 1)],
        companies=[("Acme", 1)],
    )

    text = build_telegram_alert_text(report, top_vacancies=1)

    assert "Отчет по вакансиям" in text
    assert "Топ компаний:" in text
    assert "Топ навыков:" in text
    assert "Топ вакансий:" in text
    assert "Python Developer — Acme" in text

