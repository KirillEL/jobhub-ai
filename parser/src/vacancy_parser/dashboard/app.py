from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from vacancy_parser.config import get_settings
from vacancy_parser.storage.postgresql_repository import PostgresVacancyRepository


def _to_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def _format_number(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _salary_values(vacancies_df: pd.DataFrame) -> list[float]:
    values: list[float] = []
    for _, row in vacancies_df.iterrows():
        if pd.notna(row.get("salary_from")) and pd.notna(row.get("salary_to")):
            values.append((row["salary_from"] + row["salary_to"]) / 2)
        elif pd.notna(row.get("salary_from")):
            values.append(row["salary_from"])
        elif pd.notna(row.get("salary_to")):
            values.append(row["salary_to"])
    return values


def _render_header() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        .main-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem;}
        .sub-title {color: #93a4b8; margin-bottom: 1rem;}
        </style>
        <div class="main-title">📊 Вакансии: аналитическая панель</div>
        <div class="sub-title">Мониторинг рынка, зарплат, навыков и компаний</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Аналитика вакансий", layout="wide")
    _render_header()

    settings = get_settings()
    repository = PostgresVacancyRepository(
        dsn=settings.postgres_dsn,
        connect_retries=settings.db_connect_retries,
        retry_delay_seconds=settings.db_connect_retry_delay_seconds,
    )
    repository.init_schema()

    st.sidebar.header("Настройки отчета")
    city = st.sidebar.text_input("Город", value="").strip() or None
    experience = (
        st.sidebar.text_input("Опыт (из HH, например: 1-3 или 3-6)", value="")
        .strip()
        or None
    )
    limit = st.sidebar.slider("Лимит вакансий", min_value=100, max_value=5000, value=1000, step=100)
    st.sidebar.caption("Совет: для быстрой загрузки ставьте лимит 300-1000.")

    vacancies = repository.fetch_vacancies(city=city, experience=experience, limit=limit)
    skills = repository.fetch_top_skills(limit=10, city=city, experience=experience)
    companies = repository.fetch_top_companies(limit=10, city=city, experience=experience)

    vacancy_rows = [vacancy.as_dict() for vacancy in vacancies]
    vacancies_df = _to_dataframe(vacancy_rows)
    skills_df = _to_dataframe([{"skill": s, "count": c} for s, c in skills])
    companies_df = _to_dataframe([{"company": c, "count": n} for c, n in companies])

    salary_values = _salary_values(vacancies_df) if not vacancies_df.empty else []
    median_salary = _format_number(float(pd.Series(salary_values).median())) if salary_values else "нет данных"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего вакансий", len(vacancies))
    salary_count = (
        int((vacancies_df["salary_from"].notna() | vacancies_df["salary_to"].notna()).sum())
        if not vacancies_df.empty
        else 0
    )
    col2.metric("С зарплатой", salary_count)
    col3.metric("Медианная зарплата", median_salary)
    col4.metric("Опыт", experience or "Любой")
    st.caption(
        f"Активные фильтры: город={city or 'любой'}, опыт={experience or 'любой'}, лимит={limit}"
    )

    tab_overview, tab_market, tab_table = st.tabs(["Обзор", "Графики", "Таблица вакансий"])

    with tab_overview:
        left, right = st.columns(2)
        with left:
            st.subheader("Топ навыков")
            if skills_df.empty:
                st.info("Навыки не найдены.")
            else:
                fig_skills = px.bar(
                    skills_df.sort_values("count"),
                    x="count",
                    y="skill",
                    orientation="h",
                    labels={"count": "Количество", "skill": "Навык"},
                    color="count",
                    color_continuous_scale="Blues",
                )
                fig_skills.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_skills, use_container_width=True)
        with right:
            st.subheader("Топ компаний")
            if companies_df.empty:
                st.info("Компании не найдены.")
            else:
                fig_companies = px.bar(
                    companies_df.sort_values("count"),
                    x="count",
                    y="company",
                    orientation="h",
                    labels={"count": "Количество", "company": "Компания"},
                    color="count",
                    color_continuous_scale="Teal",
                )
                fig_companies.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_companies, use_container_width=True)

    with tab_market:
        st.subheader("Распределение зарплат")
        if salary_values:
            salary_df = pd.DataFrame({"salary": salary_values})
            fig_salary = px.histogram(
                salary_df,
                x="salary",
                nbins=35,
                labels={"salary": "Зарплата"},
                color_discrete_sequence=["#3b82f6"],
            )
            fig_salary.update_layout(margin=dict(l=10, r=10, t=20, b=10), yaxis_title="Количество вакансий")
            st.plotly_chart(fig_salary, use_container_width=True)
        else:
            st.info("Для выбранных фильтров нет данных по зарплате.")

    with tab_table:
        st.subheader("Последние вакансии")
        if vacancies_df.empty:
            st.info("Нет вакансий по выбранным фильтрам.")
        else:
            display_cols = [
                "title",
                "company",
                "city",
                "experience",
                "salary_from",
                "salary_to",
                "url",
                "published_at",
            ]
            existing_cols = [col for col in display_cols if col in vacancies_df.columns]
            st.dataframe(vacancies_df[existing_cols], use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Данные обновляются после запуска парсинга и ежедневного планировщика.")


if __name__ == "__main__":
    main()

