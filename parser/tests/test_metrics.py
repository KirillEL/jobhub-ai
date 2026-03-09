from vacancy_parser.analytics.metrics import extract_salary_points, salary_summary
from vacancy_parser.models import Vacancy


def build_vacancy(salary_from=None, salary_to=None) -> Vacancy:
    return Vacancy(
        external_id="1",
        title="Python Developer",
        company="Acme",
        city="Moscow",
        salary_from=salary_from,
        salary_to=salary_to,
        currency="RUR",
        experience="1-3 years",
        schedule="Remote",
        url="https://example.com",
        published_at=None,
    )


def test_extract_salary_points() -> None:
    vacancies = [build_vacancy(100, 200), build_vacancy(150, None), build_vacancy(None, 250)]
    assert extract_salary_points(vacancies) == [150, 150, 250]


def test_salary_summary_empty() -> None:
    summary = salary_summary([build_vacancy(None, None)])
    assert summary["salary_count"] == 0
    assert summary["mean"] is None
    assert summary["median"] is None

