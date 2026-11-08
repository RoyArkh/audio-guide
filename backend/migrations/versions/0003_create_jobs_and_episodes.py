"""create jobs and episodes

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('episodes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('place_id', sa.Integer(), nullable=False),
    sa.Column('length', sa.String(length=20), nullable=False),
    sa.Column('mood', sa.String(length=30), nullable=False),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('script_text', sa.String(), nullable=False),
    sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('audio_key', sa.String(), nullable=False),
    sa.Column('duration_seconds', sa.Double(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['place_id'], ['places.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_episodes_place_id'), 'episodes', ['place_id'], unique=False)
    op.create_table('jobs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('lat', sa.Double(), nullable=False),
    sa.Column('lng', sa.Double(), nullable=False),
    sa.Column('length', sa.String(length=20), nullable=False),
    sa.Column('mood', sa.String(length=30), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('error', sa.String(), nullable=True),
    sa.Column('place_id', sa.Integer(), nullable=True),
    sa.Column('distance_m', sa.Double(), nullable=True),
    sa.Column('episode_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ),
    sa.ForeignKeyConstraint(['place_id'], ['places.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_episodes_place_id'), table_name='episodes')
    op.drop_table('episodes')
