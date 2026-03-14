from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parser_api.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="company_rel")


class Vacancy(Base):
    __tablename__ = "vacancies"
    __table_args__ = (
        Index("ix_vacancies_company_id", "company_id"),
        Index("ix_vacancies_city", "city"),
        Index("ix_vacancies_experience", "experience"),
        Index("ix_vacancies_published_at", "published_at"),
    )

    external_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[Optional[str]] = mapped_column(Text)
    company_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("companies.id"))
    city: Mapped[Optional[str]] = mapped_column(Text)
    salary_from: Mapped[Optional[float]] = mapped_column(Float)
    salary_to: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(Text)
    experience: Mapped[Optional[str]] = mapped_column(Text)
    schedule: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)

    company_rel: Mapped[Optional[Company]] = relationship(back_populates="vacancies")
    user_links: Mapped[list["UserVacancy"]] = relationship(back_populates="vacancy")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"

    vacancy_external_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("vacancies.external_id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    parse_jobs: Mapped[list["ParseJob"]] = relationship(back_populates="user")
    vacancy_links: Mapped[list["UserVacancy"]] = relationship(back_populates="user")
    telegram_report_settings: Mapped[Optional["TelegramReportSettings"]] = relationship(
        back_populates="user", uselist=False
    )


class TelegramReportSettings(Base):
    """Настройки ежедневного отчёта в Telegram (на пользователя)."""
    __tablename__ = "telegram_report_settings"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(Text)
    report_hour: Mapped[int] = mapped_column(BigInteger, nullable=False, default=9)
    report_minute: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    report_timezone: Mapped[str] = mapped_column(Text, nullable=False, default="Europe/Moscow")
    report_query: Mapped[str] = mapped_column(Text, nullable=False, default="python backend")
    report_pages: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    last_run_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="telegram_report_settings")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip: Mapped[Optional[str]] = mapped_column(Text)


class ParseJob(Base):
    __tablename__ = "parse_jobs"
    __table_args__ = (
        Index("ix_parse_jobs_user_id", "user_id"),
        Index("ix_parse_jobs_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    pages: Mapped[int] = mapped_column(BigInteger, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    parser_message: Mapped[Optional[str]] = mapped_column(Text)
    collected: Mapped[Optional[int]] = mapped_column(BigInteger)
    saved_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    new_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_count: Mapped[Optional[int]] = mapped_column(BigInteger)

    user: Mapped[User] = relationship(back_populates="parse_jobs")
    user_vacancies: Mapped[list["UserVacancy"]] = relationship(back_populates="parse_job")


class UserVacancy(Base):
    __tablename__ = "user_vacancies"
    __table_args__ = (
        Index("ix_user_vacancies_parse_job_id", "parse_job_id"),
        Index("ix_user_vacancies_user_id_ingested_at", "user_id", "ingested_at"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vacancy_external_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("vacancies.external_id", ondelete="CASCADE"),
        primary_key=True,
    )
    parse_job_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("parse_jobs.id", ondelete="SET NULL"),
    )
    ingested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="vacancy_links")
    vacancy: Mapped[Vacancy] = relationship(back_populates="user_links")
    parse_job: Mapped[Optional[ParseJob]] = relationship(back_populates="user_vacancies")
