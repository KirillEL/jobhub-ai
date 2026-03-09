from __future__ import annotations

from statistics import mean, median

from vacancy_parser.models import Vacancy


def extract_salary_points(vacancies: list[Vacancy]) -> list[float]:
    points: list[float] = []
    for vacancy in vacancies:
        if vacancy.salary_from is not None and vacancy.salary_to is not None:
            points.append((vacancy.salary_from + vacancy.salary_to) / 2)
        elif vacancy.salary_from is not None:
            points.append(vacancy.salary_from)
        elif vacancy.salary_to is not None:
            points.append(vacancy.salary_to)
    return points


def salary_summary(vacancies: list[Vacancy]) -> dict[str, float | int | None]:
    points = extract_salary_points(vacancies)
    if not points:
        return {
            "count": len(vacancies),
            "salary_count": 0,
            "mean": None,
            "median": None,
            "p90": None,
        }
    return {
        "count": len(vacancies),
        "salary_count": len(points),
        "mean": round(mean(points), 2),
        "median": round(median(points), 2),
        "p90": round(_percentile(points, 0.9), 2),
    }


def _percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("values must be non-empty")
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight

