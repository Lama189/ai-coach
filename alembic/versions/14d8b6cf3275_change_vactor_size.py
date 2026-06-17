"""change_vactor_size

Revision ID: 14d8b6cf3275
Revises: f941f60c20cb
Create Date: 2026-06-17 11:32:23.434705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '14d8b6cf3275'
down_revision: Union[str, Sequence[str], None] = 'f941f60c20cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        table_name="knowledge_chunks",
        column_name="embedding",
        type_=Vector(384),
        existing_type=Vector(768),
        nullable=False
    )


def downgrade():
    op.alter_column(
        table_name="knowledge_chunks",
        column_name="embedding",
        type_=Vector(768),
        existing_type=Vector(384),
        nullable=False
    )