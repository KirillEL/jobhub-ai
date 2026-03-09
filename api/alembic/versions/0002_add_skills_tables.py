"""add skills and vacancy_skills tables

Revision ID: 0002_add_skills_tables
Revises: 0001_initial_schema
Create Date: 2026-03-01 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_skills_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "vacancy_skills",
        sa.Column("vacancy_external_id", sa.Text(), nullable=False),
        sa.Column("skill_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_external_id"], ["vacancies.external_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("vacancy_external_id", "skill_id"),
    )
    op.create_index("ix_vacancies_company_id", "vacancies", ["company_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vacancies_company_id", table_name="vacancies")
    op.drop_table("vacancy_skills")
    op.drop_table("skills")
