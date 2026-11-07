"""create places

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_geospatial_table('places',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('wiki_lang', sa.String(length=10), nullable=False),
    sa.Column('wikipedia_page_id', sa.Integer(), nullable=False),
    sa.Column('wikidata_id', sa.String(), nullable=True),
    sa.Column('sitelinks', sa.Integer(), nullable=False),
    sa.Column('geom', Geography(geometry_type='POINT', srid=4326, dimension=2, spatial_index=False, from_text='ST_GeogFromText', name='geography', nullable=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('wiki_lang', 'wikipedia_page_id')
    )
    op.create_geospatial_index('idx_places_geom', 'places', ['geom'], unique=False, postgresql_using='gist', postgresql_ops={})
    op.create_index(op.f('ix_places_wikidata_id'), 'places', ['wikidata_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_places_wikidata_id'), table_name='places')
    op.drop_geospatial_index('idx_places_geom', table_name='places', postgresql_using='gist', column_name='geom')
    op.drop_geospatial_table('places')
