"""Enable the PostGIS and pgvector extensions.

Revision ID: 0001
Revises:
Create Date: 2026-11-05

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS: geography types and spatial queries like ST_DWithin ("within X metres").
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    # pgvector: a `vector` column type for embeddings / similarity search (used post-v1).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS postgis")
