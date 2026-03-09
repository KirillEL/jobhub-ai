from __future__ import annotations

import re

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
