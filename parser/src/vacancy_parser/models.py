from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Vacancy(BaseModel):
    model_config = ConfigDict(frozen=True)

    external_id: str
    title: str
    company: str
    city: str | None
    salary_from: float | None
    salary_to: float | None
    currency: str | None
    experience: str | None
    schedule: str | None
    url: str
    published_at: str | None
    description: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()

