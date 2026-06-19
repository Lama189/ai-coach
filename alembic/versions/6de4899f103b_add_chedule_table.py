"""add_chedule_table

Revision ID: 6de4899f103b
Revises: 14d8b6cf3275
Create Date: 2026-06-19 09:25:48.542547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = '6de4899f103b'
down_revision: Union[str, Sequence[str], None] = '14d8b6cf3275'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_schedules",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("training_day_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "day_of_week", name="uq_user_schedule_day_of_week"),
        sa.UniqueConstraint("user_id", "training_day_number", name="uq_user_schedule_training_day"),
    )


def downgrade() -> None:
    op.drop_table("user_schedules")
