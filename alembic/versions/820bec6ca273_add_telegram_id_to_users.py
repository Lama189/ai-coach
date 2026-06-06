"""add_telegram_id_to_users

Revision ID: 820bec6ca273
Revises: a4a66f116f9a
Create Date: 2026-06-06 05:10:13.214330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '820bec6ca273'
down_revision: Union[str, Sequence[str], None] = 'a4a66f116f9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users', 
        sa.Column('telegram_id', sa.BigInteger(), nullable=True)
    )
    
    op.create_index(
        op.f('ix_users_telegram_id'), 
        'users', 
        ['telegram_id'], 
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_column('users', 'telegram_id')
