from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from parser_api.db.models import Company, Skill, UserVacancy, Vacancy, VacancySkill
from parser_api.services.skills import extract_known_skills


class VacancyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        user_id: int,
        city: str | None = None,
        experience: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Vacancy], int]:
        stmt = (
            select(Vacancy)
            .join(UserVacancy, UserVacancy.vacancy_external_id == Vacancy.external_id)
            .options(joinedload(Vacancy.company_rel))
            .where(UserVacancy.user_id == user_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(UserVacancy)
            .join(Vacancy, Vacancy.external_id == UserVacancy.vacancy_external_id)
            .where(UserVacancy.user_id == user_id)
        )

        if city:
            stmt = stmt.where(Vacancy.city == city)
            count_stmt = count_stmt.where(Vacancy.city == city)
        if experience:
            stmt = stmt.where(Vacancy.experience == experience)
            count_stmt = count_stmt.where(Vacancy.experience == experience)
        if search:
            pattern = f"%{search}%"
            condition = or_(Vacancy.title.ilike(pattern), Vacancy.description.ilike(pattern))
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        stmt = stmt.order_by(UserVacancy.ingested_at.desc()).offset(offset).limit(limit)

        items = (await self.db.scalars(stmt)).all()
        total = await self.db.scalar(count_stmt) or 0
        return items, int(total)

    async def get_by_external_id(self, external_id: str, user_id: int) -> Vacancy | None:
        stmt = (
            select(Vacancy)
            .join(UserVacancy, UserVacancy.vacancy_external_id == Vacancy.external_id)
            .options(joinedload(Vacancy.company_rel))
            .where(Vacancy.external_id == external_id)
            .where(UserVacancy.user_id == user_id)
        )
        return await self.db.scalar(stmt)

    async def list_existing_external_ids(self, external_ids: list[str], user_id: int) -> set[str]:
        normalized_ids = [item.strip() for item in external_ids if item and item.strip()]
        if not normalized_ids:
            return set()
        stmt = select(UserVacancy.vacancy_external_id).where(
            UserVacancy.user_id == user_id,
            UserVacancy.vacancy_external_id.in_(normalized_ids),
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return set(rows)

    async def fetch_top_skills(
        self,
        user_id: int,
        city: str | None = None,
        experience: str | None = None,
        search: str | None = None,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Skill.name, func.count(VacancySkill.skill_id).label("occurrences"))
            .select_from(VacancySkill)
            .join(Skill, Skill.id == VacancySkill.skill_id)
            .join(Vacancy, Vacancy.external_id == VacancySkill.vacancy_external_id)
            .join(UserVacancy, UserVacancy.vacancy_external_id == Vacancy.external_id)
            .where(UserVacancy.user_id == user_id)
        )

        if city:
            stmt = stmt.where(Vacancy.city == city)
        if experience:
            stmt = stmt.where(Vacancy.experience == experience)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Vacancy.title.ilike(pattern), Vacancy.description.ilike(pattern)))

        stmt = (
            stmt.group_by(Skill.name)
            .order_by(func.count(VacancySkill.skill_id).desc(), Skill.name.asc())
            .limit(limit)
        )

        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def fetch_top_companies(
        self,
        user_id: int,
        city: str | None = None,
        experience: str | None = None,
        search: str | None = None,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Company.name, func.count(Vacancy.external_id).label("vacancy_count"))
            .select_from(Vacancy)
            .join(UserVacancy, UserVacancy.vacancy_external_id == Vacancy.external_id)
            .join(Company, Company.id == Vacancy.company_id)
            .where(UserVacancy.user_id == user_id)
        )

        if city:
            stmt = stmt.where(Vacancy.city == city)
        if experience:
            stmt = stmt.where(Vacancy.experience == experience)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Vacancy.title.ilike(pattern), Vacancy.description.ilike(pattern)))

        stmt = (
            stmt.group_by(Company.name)
            .order_by(func.count(Vacancy.external_id).desc(), Company.name.asc())
            .limit(limit)
        )

        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def upsert_many(
        self,
        vacancies: list[dict[str, Any]],
        user_id: int,
        parse_job_id: int | None,
    ) -> int:
        if not vacancies:
            return 0

        try:
            prepared_rows = [self._prepare_vacancy_row(item) for item in vacancies]
            prepared_rows = [row for row in prepared_rows if row["external_id"] and row["title"] and row["url"]]
            prepared_rows = self._deduplicate_by_external_id(prepared_rows)
            if not prepared_rows:
                return 0

            company_names = sorted({self._normalize_company_name(row.get("company")) for row in prepared_rows})
            await self.db.execute(
                insert(Company)
                .values([{"name": name} for name in company_names])
                .on_conflict_do_nothing(index_elements=[Company.name])
            )

            company_rows = await self.db.execute(
                select(Company.id, Company.name).where(Company.name.in_(company_names))
            )
            company_map = {name: company_id for company_id, name in company_rows.all()}

            vacancy_values = []
            for row in prepared_rows:
                normalized_company = self._normalize_company_name(row.get("company"))
                vacancy_values.append(
                    {
                        "external_id": row["external_id"],
                        "title": row["title"],
                        "company": normalized_company,
                        "company_id": company_map.get(normalized_company),
                        "city": row.get("city"),
                        "salary_from": row.get("salary_from"),
                        "salary_to": row.get("salary_to"),
                        "currency": row.get("currency"),
                        "experience": row.get("experience"),
                        "schedule": row.get("schedule"),
                        "url": row["url"],
                        "published_at": row.get("published_at"),
                        "description": row.get("description"),
                    }
                )

            upsert_stmt = insert(Vacancy).values(vacancy_values)
            await self.db.execute(
                upsert_stmt.on_conflict_do_update(
                    index_elements=[Vacancy.external_id],
                    set_={
                        "title": upsert_stmt.excluded.title,
                        "company": upsert_stmt.excluded.company,
                        "company_id": upsert_stmt.excluded.company_id,
                        "city": upsert_stmt.excluded.city,
                        "salary_from": upsert_stmt.excluded.salary_from,
                        "salary_to": upsert_stmt.excluded.salary_to,
                        "currency": upsert_stmt.excluded.currency,
                        "experience": upsert_stmt.excluded.experience,
                        "schedule": upsert_stmt.excluded.schedule,
                        "url": upsert_stmt.excluded.url,
                        "published_at": upsert_stmt.excluded.published_at,
                        "description": upsert_stmt.excluded.description,
                    },
                )
            )

            await self._upsert_skills_and_relations(prepared_rows)
            await self._upsert_user_vacancies(
                vacancies=prepared_rows,
                user_id=user_id,
                parse_job_id=parse_job_id,
            )
            await self.db.commit()
            return len(vacancy_values)
        except Exception:
            await self.db.rollback()
            raise

    async def delete_user_vacancies(self, user_id: int) -> int:
        result = await self.db.execute(delete(UserVacancy).where(UserVacancy.user_id == user_id))
        await self.db.commit()
        return int(result.rowcount or 0)

    async def list_titles_urls_by_parse_job(
        self, user_id: int, parse_job_id: int, limit: int = 5
    ) -> list[tuple[str, str]]:
        """Вакансии, добавленные в рамках этого parse job (для отчёта в Telegram)."""
        stmt = (
            select(Vacancy.title, Vacancy.url)
            .join(UserVacancy, UserVacancy.vacancy_external_id == Vacancy.external_id)
            .where(
                UserVacancy.user_id == user_id,
                UserVacancy.parse_job_id == parse_job_id,
            )
            .order_by(UserVacancy.ingested_at.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row[0] or "", row[1] or "") for row in rows]


    async def _upsert_skills_and_relations(self, vacancies: list[dict[str, Any]]) -> None:
        all_skills = sorted(
            {skill for vacancy in vacancies for skill in extract_known_skills(vacancy.get("description"))}
        )
        if not all_skills:
            return

        await self.db.execute(
            insert(Skill)
            .values([{"name": skill} for skill in all_skills])
            .on_conflict_do_nothing(index_elements=[Skill.name])
        )
        skill_rows = await self.db.execute(select(Skill.id, Skill.name).where(Skill.name.in_(all_skills)))
        skill_map = {name: skill_id for skill_id, name in skill_rows.all()}

        relation_values = []
        seen_relations: set[tuple[str, int]] = set()
        for vacancy in vacancies:
            external_id = vacancy["external_id"]
            for skill in extract_known_skills(vacancy.get("description")):
                skill_id = skill_map.get(skill)
                if skill_id is None:
                    continue
                relation = (external_id, skill_id)
                if relation in seen_relations:
                    continue
                seen_relations.add(relation)
                relation_values.append({"vacancy_external_id": external_id, "skill_id": skill_id})

        if relation_values:
            await self.db.execute(
                insert(VacancySkill)
                .values(relation_values)
                .on_conflict_do_nothing(
                    index_elements=[VacancySkill.vacancy_external_id, VacancySkill.skill_id]
                )
            )

    async def _upsert_user_vacancies(
        self,
        vacancies: list[dict[str, Any]],
        user_id: int,
        parse_job_id: int | None,
    ) -> None:
        now = datetime.now(timezone.utc)
        relation_values = [
            {
                "user_id": user_id,
                "vacancy_external_id": item["external_id"],
                "parse_job_id": parse_job_id,
                "ingested_at": now,
            }
            for item in vacancies
            if item.get("external_id")
        ]
        if not relation_values:
            return

        relation_insert = insert(UserVacancy).values(relation_values)
        await self.db.execute(
            relation_insert.on_conflict_do_update(
                index_elements=[UserVacancy.user_id, UserVacancy.vacancy_external_id],
                set_={
                    "parse_job_id": relation_insert.excluded.parse_job_id,
                    "ingested_at": relation_insert.excluded.ingested_at,
                },
            )
        )

    @staticmethod
    def _normalize_company_name(name: str | None) -> str:
        normalized = (name or "").strip()
        return normalized if normalized else "Unknown"

    @staticmethod
    def _prepare_vacancy_row(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_id": str(item.get("external_id", "")).strip(),
            "title": str(item.get("title", "")).strip(),
            "company": item.get("company"),
            "city": item.get("city"),
            "salary_from": item.get("salary_from"),
            "salary_to": item.get("salary_to"),
            "currency": item.get("currency"),
            "experience": item.get("experience"),
            "schedule": item.get("schedule"),
            "url": str(item.get("url", "")).strip(),
            "published_at": item.get("published_at"),
            "description": item.get("description"),
        }

    @staticmethod
    def _deduplicate_by_external_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # ON CONFLICT ... DO UPDATE fails if one INSERT contains duplicate conflict keys.
        # Keep the last occurrence so the freshest payload wins.
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            deduped[row["external_id"]] = row
        return list(deduped.values())
