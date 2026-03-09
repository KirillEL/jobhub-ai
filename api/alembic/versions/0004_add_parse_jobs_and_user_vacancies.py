"""add parse_jobs and user_vacancies tables

Revision ID: 0004_parse_jobs_user_vac
Revises: 0003_add_auth_tables
Create Date: 2026-03-03 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_parse_jobs_user_vac"
down_revision: Union[str, None] = "0003_add_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parse_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("pages", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parse_jobs_started_at", "parse_jobs", ["started_at"], unique=False)
    op.create_index("ix_parse_jobs_user_id", "parse_jobs", ["user_id"], unique=False)

    op.create_table(
        "user_vacancies",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("vacancy_external_id", sa.Text(), nullable=False),
        sa.Column("parse_job_id", sa.BigInteger(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parse_job_id"], ["parse_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["vacancy_external_id"], ["vacancies.external_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "vacancy_external_id"),
    )
    op.create_index("ix_user_vacancies_parse_job_id", "user_vacancies", ["parse_job_id"], unique=False)
    op.create_index(
        "ix_user_vacancies_user_id_ingested_at",
        "user_vacancies",
        ["user_id", "ingested_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_vacancies_user_id_ingested_at", table_name="user_vacancies")
    op.drop_index("ix_user_vacancies_parse_job_id", table_name="user_vacancies")
    op.drop_table("user_vacancies")
    op.drop_index("ix_parse_jobs_user_id", table_name="parse_jobs")
    op.drop_index("ix_parse_jobs_started_at", table_name="parse_jobs")
    op.drop_table("parse_jobs")
