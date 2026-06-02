"""add_pgvector_and_insights

Revision ID: 72ca51a380ee
Revises: 957fe72dfc47
Create Date: 2026-06-02 09:16:59.402119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '72ca51a380ee'
down_revision: Union[str, Sequence[str], None] = '957fe72dfc47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS VECTOR")

    op.add_column('exercises', sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True))
    op.execute("ALTER TABLE exercises ALTER COLUMN embedding TYPE vector(384);")

    op.create_table(
        'user_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute("ALTER TABLE user_insights ALTER COLUMN embedding TYPE vector(384);")
    op.execute("CREATE INDEX IF NOT EXISTS exercises_embedding_hnsw_idx ON exercises USING hnsw (embedding vector_cosine_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS user_insights_embedding_hnsw_idx ON user_insights USING hnsw (embedding vector_cosine_ops);")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS user_insights_embedding_hnsw_idx;")
    op.execute("DROP INDEX IF EXISTS exercises_embedding_hnsw_idx;")

    op.drop_table('user_insights')
    op.drop_column('exercises', 'embedding')

    op.execute("DROP EXTENSION IF EXISTS vector;")