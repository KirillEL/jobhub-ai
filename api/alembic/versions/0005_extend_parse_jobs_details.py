"""extend parse_jobs with result details

Revision ID: 0005_extend_parse_jobs_details
Revises: 0004_parse_jobs_user_vac
Create Date: 2026-03-09 11:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_extend_parse_jobs_details"
down_revision: Union[str, None] = "0004_parse_jobs_user_vac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("parse_jobs", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_index(
        "uq_parse_jobs_user_id_idempotency_key",
        "parse_jobs",
        ["user_id", "idempotency_key"],
        unique=True,
    )
    op.add_column("parse_jobs", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("parse_jobs", sa.Column("parser_message", sa.Text(), nullable=True))
    op.add_column("parse_jobs", sa.Column("collected", sa.BigInteger(), nullable=True))
    op.add_column("parse_jobs", sa.Column("saved_count", sa.BigInteger(), nullable=True))
    op.add_column("parse_jobs", sa.Column("new_count", sa.BigInteger(), nullable=True))
    op.add_column("parse_jobs", sa.Column("updated_count", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_index("uq_parse_jobs_user_id_idempotency_key", table_name="parse_jobs")
    op.drop_column("parse_jobs", "idempotency_key")
    op.drop_column("parse_jobs", "updated_count")
    op.drop_column("parse_jobs", "new_count")
    op.drop_column("parse_jobs", "saved_count")
    op.drop_column("parse_jobs", "collected")
    op.drop_column("parse_jobs", "parser_message")
    op.drop_column("parse_jobs", "error_message")
