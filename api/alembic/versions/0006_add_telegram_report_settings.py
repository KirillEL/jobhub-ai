"""add telegram_report_settings table

Revision ID: 0006_telegram_report
Revises: 0005_extend_parse_jobs_details
Create Date: 2026-03-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_telegram_report"
down_revision: Union[str, None] = "0005_extend_parse_jobs_details"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_report_settings",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("telegram_chat_id", sa.Text(), nullable=True),
        sa.Column("report_hour", sa.BigInteger(), nullable=False, server_default="9"),
        sa.Column("report_minute", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("report_timezone", sa.Text(), nullable=False, server_default="Europe/Moscow"),
        sa.Column("report_query", sa.Text(), nullable=False, server_default="python backend"),
        sa.Column("report_pages", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("telegram_report_settings")
