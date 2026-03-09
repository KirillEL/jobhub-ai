"""create initial companies and vacancies tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "vacancies",
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("salary_from", sa.Float(), nullable=True),
        sa.Column("salary_to", sa.Float(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("experience", sa.Text(), nullable=True),
        sa.Column("schedule", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("external_id"),
    )
    op.create_index("ix_vacancies_city", "vacancies", ["city"], unique=False)
    op.create_index("ix_vacancies_experience", "vacancies", ["experience"], unique=False)
    op.create_index("ix_vacancies_published_at", "vacancies", ["published_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vacancies_published_at", table_name="vacancies")
    op.drop_index("ix_vacancies_experience", table_name="vacancies")
    op.drop_index("ix_vacancies_city", table_name="vacancies")
    op.drop_table("vacancies")
    op.drop_table("companies")
