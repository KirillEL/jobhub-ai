from __future__ import annotations

from pathlib import Path

import pandas as pd

from vacancy_parser.models import Vacancy


class CsvVacancyRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, vacancies: list[Vacancy]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame([vacancy.as_dict() for vacancy in vacancies])
        frame.drop_duplicates(subset=["external_id"], inplace=True)
        frame.to_csv(self.path, index=False)

