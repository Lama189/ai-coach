"""add_tag_for_user_insights

Revision ID: 430365e535da
Revises: 40675a9def49
Create Date: 2026-06-08 09:15:03.845299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '430365e535da'
down_revision: Union[str, Sequence[str], None] = '40675a9def49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sa_enum = sa.Enum(
        "injury",
        "progress", 
        "fatigue",
        "preference",
        "schedule",
        "nutrition",
        "technique",
        "mental",
        name="tag",
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'user_insights', 
        sa.Column(
            "tag", 
            sa_enum, 
            nullable=False
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_insights", "tag")
    op.execute("DROP TYPE tag")
    
