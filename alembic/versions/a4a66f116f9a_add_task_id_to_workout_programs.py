"""add_task_id_to_workout_programs

Revision ID: a4a66f116f9a
Revises: 72ca51a380ee
Create Date: 2026-06-05 08:15:57.533338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a4a66f116f9a'
down_revision: Union[str, Sequence[str], None] = '72ca51a380ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'workout_programs', 
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    op.create_index(
        op.f('ix_workout_programs_task_id'), 
        'workout_programs', 
        ['task_id'], 
        unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_workout_programs_task_id'), table_name='workout_programs')
    op.drop_column('workout_programs', 'task_id')