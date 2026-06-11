"""create_intent_table_add_location_to_profiles

Revision ID: f40912a07b8c
Revises: 430365e535da
Create Date: 2026-06-11 13:25:40.359623

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'f40912a07b8c'
down_revision: Union[str, Sequence[str], None] = '430365e535da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    location_enum = sa.Enum('gym', 'home', 'outdoor', name='location')
    location_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'user_profiles',
        sa.Column('location', location_enum, nullable=True),
    )

    op.create_table(
        'user_intents',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('goal', sa.String(), nullable=False),
        sa.Column('constraints', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('focus_areas', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('location', sa.String(20), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('program_id', sa.UUID(), sa.ForeignKey('workout_programs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('user_intents')
    op.drop_column('user_profiles', 'location')
    op.execute("DROP TYPE IF EXISTS location")