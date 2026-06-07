"""make_profile_fields_nullable

Revision ID: 4a4edcc20beb
Revises: 175b38ea5ee9
Create Date: 2026-06-06 12:41:44.787761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a4edcc20beb'
down_revision: Union[str, Sequence[str], None] = '175b38ea5ee9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('user_profiles', 'gender', existing_type=sa.Enum(name='gender'), nullable=True)
    op.alter_column('user_profiles', 'age', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_profiles', 'height_cm', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_profiles', 'weight_kg', existing_type=sa.Float(), nullable=True)
    op.alter_column('user_profiles', 'goal', existing_type=sa.Enum(name='fitness_goal'), nullable=True)
    op.alter_column('user_profiles', 'experience_level', existing_type=sa.Enum(name='experience_level'), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user_profiles', 'gender', existing_type=sa.Enum(name='gender'), nullable=False)
    op.alter_column('user_profiles', 'age', existing_type=sa.Integer(), nullable=False)
    op.alter_column('user_profiles', 'height_cm', existing_type=sa.Integer(), nullable=False)
    op.alter_column('user_profiles', 'weight_kg', existing_type=sa.Float(), nullable=False)
    op.alter_column('user_profiles', 'goal', existing_type=sa.Enum(name='fitness_goal'), nullable=False)
    op.alter_column('user_profiles', 'experience_level', existing_type=sa.Enum(name='experience_level'), nullable=False)
