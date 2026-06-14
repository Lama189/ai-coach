"""add_array_move_patterns_for_exerc

Revision ID: 4bd86aaefaeb
Revises: 056eb99961f0
Create Date: 2026-06-14 07:31:04.916809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4bd86aaefaeb'
down_revision: Union[str, Sequence[str], None] = '056eb99961f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("exercises", "movement_pattern")
    op.add_column("exercises", sa.Column(
        "movement_patterns",
        postgresql.ARRAY(sa.String(50)),
        nullable=False,
        server_default="{}"
    ))
   

def downgrade() -> None:
    op.drop_column("exercises", "movement_patterns")

    op.add_column("exercises", sa.Column(
        "movement_pattern", 
        sa.String(50), 
        nullable=False 
    ))
