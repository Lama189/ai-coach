"""add_status_to_sessions

Revision ID: 40675a9def49
Revises: 4a4edcc20beb
Create Date: 2026-06-07 12:52:47.553796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '40675a9def49'
down_revision: Union[str, Sequence[str], None] = '4a4edcc20beb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sessions', 
        sa.Column(
            "status", 
            sa.String(20), 
            nullable=False, 
            server_default="active"
        )
    )

    op.alter_column(
        "sessions",
        "finished_at",
        nullable=True,
        existing_type=sa.DateTime(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "sessions",
        "finished_at",
        nullable=False,
        existing_type=sa.DateTime(timezone=True),
    )

    op.drop_column("sessions", "status")
