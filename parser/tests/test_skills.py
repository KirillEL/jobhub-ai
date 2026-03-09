from vacancy_parser.analytics.skills import top_skills
from vacancy_parser.models import Vacancy


def test_top_skills() -> None:
    vacancies = [
        Vacancy(
            external_id="1",
            title="Backend Developer",
            company="Acme",
            city="Moscow",
            salary_from=None,
            salary_to=None,
            currency=None,
            experience=None,
            schedule=None,
            url="https://example.com/1",
            published_at=None,
            description="Python FastAPI SQL Docker",
        ),
        Vacancy(
            external_id="2",
            title="Data Engineer",
            company="Acme",
            city="SPB",
            salary_from=None,
            salary_to=None,
            currency=None,
            experience=None,
            schedule=None,
            url="https://example.com/2",
            published_at=None,
            description="Python SQL Airflow",
        ),
    ]
    assert top_skills(vacancies, limit=3) == [("python", 2), ("sql", 2), ("fastapi", 1)]

