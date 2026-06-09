"""field_polygon: geometry -> geography(Polygon, 4326)

Revision ID: 8196922098a6
Revises: a7c4e9f12b80
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8196922098a6'
down_revision: Union[str, Sequence[str], None] = 'a7c4e9f12b80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'farms',
        'field_polygon',
        type_=geoalchemy2.types.Geography(geometry_type='POLYGON', srid=4326, spatial_index=False),
        postgresql_using='field_polygon::geography(Polygon, 4326)',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'farms',
        'field_polygon',
        type_=geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, spatial_index=False),
        postgresql_using='field_polygon::geometry(Polygon, 4326)',
    )
