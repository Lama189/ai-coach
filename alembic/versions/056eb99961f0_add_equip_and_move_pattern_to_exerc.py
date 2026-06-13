"""add_equip_and_move_pattern_to_exerc

Revision ID: 056eb99961f0
Revises: f40912a07b8c
Create Date: 2026-06-13 08:16:39.264735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '056eb99961f0'
down_revision: Union[str, Sequence[str], None] = 'f40912a07b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("equipment", sa.String(length=50), nullable=False, server_default="bodyweight"),
    )

    op.add_column(
        "exercises",
        sa.Column("movement_pattern", sa.String(length=50), nullable=False, server_default="push_horizontal"),
    )

    op.alter_column("exercises", "equipment", server_default=None)
    op.alter_column("exercises", "movement_pattern", server_default=None)


def downgrade() -> None:
    op.drop_column("exercises", "movement_pattern")
    op.drop_column("exercises", "equipment")
