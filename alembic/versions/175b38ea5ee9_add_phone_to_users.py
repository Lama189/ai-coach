"""add_phone_to_users

Revision ID: 175b38ea5ee9
Revises: 820bec6ca273
Create Date: 2026-06-06 06:36:08.568312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '175b38ea5ee9'
down_revision: Union[str, Sequence[str], None] = '820bec6ca273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('phone', sa.String(length=50), nullable=False)
    )
    

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'phone')
