from __future__ import annotations

import re
from collections import Counter

from vacancy_parser.models import Vacancy

COMMON_SKILLS = {
    "python",
    "sql",
    "docker",
    "kubernetes",
    "fastapi",
    "django",
    "flask",
    "pandas",
    "numpy",
    "git",
    "airflow",
    "spark",
    "linux",
    "redis",
    "postgresql",
    "clickhouse",
}


def extract_known_skills(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]*", text.lower())
    return {token for token in tokens if token in COMMON_SKILLS}


def top_skills(vacancies: list[Vacancy], limit: int = 10) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for vacancy in vacancies:
        for skill in extract_known_skills(vacancy.description):
            counter[skill] += 1
    return counter.most_common(limit)

