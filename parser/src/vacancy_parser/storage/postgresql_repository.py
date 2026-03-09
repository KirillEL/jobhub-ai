from __future__ import annotations

import time

import psycopg

from vacancy_parser.analytics.skills import extract_known_skills
from vacancy_parser.models import Vacancy


class PostgresVacancyRepository:
    def __init__(
        self,
        dsn: str,
        connect_retries: int = 10,
        retry_delay_seconds: float = 2.0,
    ) -> None:
        self.dsn = dsn
        self.connect_retries = connect_retries
        self.retry_delay_seconds = retry_delay_seconds

    def init_schema(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS companies (
                        id BIGSERIAL PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vacancies (
                        external_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        company TEXT,
                        company_id BIGINT REFERENCES companies(id),
                        city TEXT,
                        salary_from DOUBLE PRECISION,
                        salary_to DOUBLE PRECISION,
                        currency TEXT,
                        experience TEXT,
                        schedule TEXT,
                        url TEXT NOT NULL,
                        published_at TEXT,
                        description TEXT
                    )
                    """
                )
                # Backward-compatible migration for early schema versions.
                cursor.execute("ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS company_id BIGINT")
                cursor.execute("ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS company TEXT")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS skills (
                        id BIGSERIAL PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vacancy_skills (
                        vacancy_external_id TEXT NOT NULL REFERENCES vacancies(external_id) ON DELETE CASCADE,
                        skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
                        PRIMARY KEY (vacancy_external_id, skill_id)
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_vacancies_company_id ON vacancies(company_id)"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_city ON vacancies(city)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_vacancies_experience ON vacancies(experience)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_vacancies_published_at ON vacancies(published_at)"
                )
            connection.commit()

    def upsert_many(self, vacancies: list[Vacancy]) -> None:
        if not vacancies:
            return

        with self._connect() as connection:
            with connection.cursor() as cursor:
                company_map = self._upsert_companies(cursor, vacancies)
                self._upsert_vacancies(cursor, vacancies, company_map)
                self._upsert_skills(cursor, vacancies)
                self._upsert_vacancy_skills(cursor, vacancies)
            connection.commit()

    def fetch_vacancies(
        self,
        city: str | None = None,
        experience: str | None = None,
        limit: int = 1000,
    ) -> list[Vacancy]:
        query = """
            SELECT
                v.external_id,
                v.title,
                c.name AS company,
                v.city,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.experience,
                v.schedule,
                v.url,
                v.published_at,
                v.description
            FROM vacancies v
            JOIN companies c ON c.id = v.company_id
        """
        where_sql, params = self._build_filters(city=city, experience=experience)
        query += where_sql
        query += " ORDER BY v.published_at DESC NULLS LAST LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return [
            Vacancy(
                external_id=row[0],
                title=row[1],
                company=row[2],
                city=row[3],
                salary_from=row[4],
                salary_to=row[5],
                currency=row[6],
                experience=row[7],
                schedule=row[8],
                url=row[9],
                published_at=row[10],
                description=row[11],
            )
            for row in rows
        ]

    def fetch_top_skills(
        self, limit: int = 10, city: str | None = None, experience: str | None = None
    ) -> list[tuple[str, int]]:
        query = """
            SELECT s.name, COUNT(*)::INT AS occurrences
            FROM vacancy_skills vs
            JOIN skills s ON s.id = vs.skill_id
            JOIN vacancies v ON v.external_id = vs.vacancy_external_id
        """
        where_sql, params = self._build_filters(city=city, experience=experience, alias="v")
        query += where_sql
        query += " GROUP BY s.name ORDER BY occurrences DESC, s.name ASC LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

    def fetch_top_companies(
        self, limit: int = 5, city: str | None = None, experience: str | None = None
    ) -> list[tuple[str, int]]:
        query = """
            SELECT c.name, COUNT(*)::INT AS vacancies_count
            FROM vacancies v
            JOIN companies c ON c.id = v.company_id
        """
        where_sql, params = self._build_filters(city=city, experience=experience, alias="v")
        query += where_sql
        query += " GROUP BY c.name ORDER BY vacancies_count DESC, c.name ASC LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [(row[0], row[1]) for row in rows]

    def _upsert_companies(
        self, cursor: psycopg.Cursor[tuple], vacancies: list[Vacancy]
    ) -> dict[str, int]:
        company_names = sorted({self._normalize_company_name(v.company) for v in vacancies})
        company_map: dict[str, int] = {}
        for name in company_names:
            cursor.execute(
                """
                INSERT INTO companies (name)
                VALUES (%s)
                ON CONFLICT(name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (name,),
            )
            company_map[name] = cursor.fetchone()[0]
        return company_map

    def _upsert_vacancies(
        self, cursor: psycopg.Cursor[tuple], vacancies: list[Vacancy], company_map: dict[str, int]
    ) -> None:
        vacancy_rows = [
            (
                v.external_id,
                v.title,
                self._normalize_company_name(v.company),
                company_map[self._normalize_company_name(v.company)],
                v.city,
                v.salary_from,
                v.salary_to,
                v.currency,
                v.experience,
                v.schedule,
                v.url,
                v.published_at,
                v.description,
            )
            for v in vacancies
        ]
        cursor.executemany(
            """
            INSERT INTO vacancies (
                external_id, title, company, company_id, city, salary_from, salary_to, currency,
                experience, schedule, url, published_at, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(external_id) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                company_id = excluded.company_id,
                city = excluded.city,
                salary_from = excluded.salary_from,
                salary_to = excluded.salary_to,
                currency = excluded.currency,
                experience = excluded.experience,
                schedule = excluded.schedule,
                url = excluded.url,
                published_at = excluded.published_at,
                description = excluded.description
            """,
            vacancy_rows,
        )

    def _upsert_skills(self, cursor: psycopg.Cursor[tuple], vacancies: list[Vacancy]) -> None:
        all_skills = sorted(
            {skill for vacancy in vacancies for skill in extract_known_skills(vacancy.description)}
        )
        if not all_skills:
            return
        cursor.executemany(
            """
            INSERT INTO skills (name)
            VALUES (%s)
            ON CONFLICT(name) DO NOTHING
            """,
            [(skill,) for skill in all_skills],
        )

    def _upsert_vacancy_skills(self, cursor: psycopg.Cursor[tuple], vacancies: list[Vacancy]) -> None:
        skill_map = self._fetch_skill_map(cursor)
        relation_rows: list[tuple[str, int]] = []
        for vacancy in vacancies:
            for skill in extract_known_skills(vacancy.description):
                skill_id = skill_map.get(skill)
                if skill_id is not None:
                    relation_rows.append((vacancy.external_id, skill_id))
        if not relation_rows:
            return
        cursor.executemany(
            """
            INSERT INTO vacancy_skills (vacancy_external_id, skill_id)
            VALUES (%s, %s)
            ON CONFLICT(vacancy_external_id, skill_id) DO NOTHING
            """,
            relation_rows,
        )

    def _fetch_skill_map(self, cursor: psycopg.Cursor[tuple]) -> dict[str, int]:
        cursor.execute("SELECT id, name FROM skills")
        rows = cursor.fetchall()
        return {name: skill_id for skill_id, name in rows}

    @staticmethod
    def _build_filters(
        city: str | None, experience: str | None, alias: str = "v"
    ) -> tuple[str, list[object]]:
        conditions: list[str] = []
        params: list[object] = []
        if city:
            conditions.append(f"{alias}.city = %s")
            params.append(city)
        if experience:
            conditions.append(f"{alias}.experience = %s")
            params.append(experience)
        if not conditions:
            return "", params
        return f" WHERE {' AND '.join(conditions)}", params

    @staticmethod
    def _normalize_company_name(name: str) -> str:
        normalized = name.strip()
        return normalized if normalized else "Unknown"

    def _connect(self) -> psycopg.Connection:
        last_error: Exception | None = None
        for attempt in range(1, self.connect_retries + 1):
            try:
                return psycopg.connect(self.dsn)
            except psycopg.OperationalError as exc:
                last_error = exc
                if attempt == self.connect_retries:
                    break
                print(
                    "PostgreSQL connection failed "
                    f"(attempt {attempt}/{self.connect_retries}). "
                    f"Retry in {self.retry_delay_seconds}s..."
                )
                time.sleep(self.retry_delay_seconds)
        raise RuntimeError(
            f"Could not connect to PostgreSQL after {self.connect_retries} attempts"
        ) from last_error

