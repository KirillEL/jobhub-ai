from __future__ import annotations

from abc import ABC, abstractmethod

from vacancy_parser.models import Vacancy


class VacancyProvider(ABC):
    @abstractmethod
    def fetch(
        self,
        query: str,
        pages: int = 1,
        *,
        city: str | None = None,
        experience: str | None = None,
        schedule: str | None = None,
    ) -> list[Vacancy]:
        raise NotImplementedError

