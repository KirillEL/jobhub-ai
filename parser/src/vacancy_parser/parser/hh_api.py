from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from vacancy_parser.models import Vacancy
from vacancy_parser.parser.base import VacancyProvider

HH_SEARCH_URL = "https://api.hh.ru/vacancies"
# Limit concurrent requests to avoid HH rate limits
MAX_CONCURRENT_PAGES = 4


class HeadHunterApiProvider(VacancyProvider):
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def _fetch_page(self, query: str, page: int) -> tuple[int, list[Vacancy]]:
        """Fetch a single page. Returns (total_pages, vacancies)."""
        payload = {"text": query, "page": page, "per_page": 100}
        response = requests.get(
            HH_SEARCH_URL, params=payload, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        total_pages = data.get("pages", 1)
        return total_pages, self._map_items(items)

    def fetch(
        self,
        query: str,
        pages: int = 1,
        *,
        city: str | None = None,
        experience: str | None = None,
        schedule: str | None = None,
    ) -> list[Vacancy]:
        if pages <= 0:
            return []

        # First page to get total_pages and first batch
        total_pages, first_vacancies = self._fetch_page(query, 0)
        vacancies: list[Vacancy] = list(first_vacancies)
        need_pages = min(pages, total_pages)

        if need_pages <= 1:
            return vacancies

        # Fetch remaining pages in parallel with limited concurrency
        page_results: dict[int, list[Vacancy]] = {0: first_vacancies}
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PAGES) as executor:
            future_to_page = {
                executor.submit(self._fetch_page, query, p): p
                for p in range(1, need_pages)
            }
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    _, items = future.result()
                    page_results[page] = items
                except Exception:
                    raise

        for p in range(1, need_pages):
            vacancies.extend(page_results.get(p, []))

        return self._apply_filters(
            vacancies,
            city=city,
            experience=experience,
            schedule=schedule,
        )

    @staticmethod
    def _apply_filters(
        vacancies: list[Vacancy],
        *,
        city: str | None,
        experience: str | None,
        schedule: str | None,
    ) -> list[Vacancy]:
        if not city and not experience and not schedule:
            return vacancies

        def matches(value: str | None, expected: str | None) -> bool:
            if not expected:
                return True
            return (value or "").strip().casefold() == expected.strip().casefold()

        return [
            item
            for item in vacancies
            if matches(item.city, city)
            and matches(item.experience, experience)
            and matches(item.schedule, schedule)
        ]

    def _map_items(self, items: list[dict[str, Any]]) -> list[Vacancy]:
        mapped: list[Vacancy] = []
        for item in items:
            salary = item.get("salary") or {}
            employer = item.get("employer") or {}
            area = item.get("area") or {}
            exp = item.get("experience") or {}
            schedule = item.get("schedule") or {}
            snippet = item.get("snippet") or {}
            description = " ".join(
                part for part in [snippet.get("requirement"), snippet.get("responsibility")] if part
            )

            mapped.append(
                Vacancy(
                    external_id=str(item.get("id", "")),
                    title=item.get("name", "").strip(),
                    company=employer.get("name", "").strip(),
                    city=area.get("name"),
                    salary_from=salary.get("from"),
                    salary_to=salary.get("to"),
                    currency=salary.get("currency"),
                    experience=exp.get("name"),
                    schedule=schedule.get("name"),
                    url=item.get("alternate_url", ""),
                    published_at=item.get("published_at"),
                    description=description or None,
                )
            )
        return mapped

