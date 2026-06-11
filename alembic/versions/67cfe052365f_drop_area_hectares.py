"""drop legacy area_hectares column

Revision ID: 67cfe052365f
Revises: f4a8d1c92e37
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67cfe052365f'
down_revision: Union[str, Sequence[str], None] = 'f4a8d1c92e37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 1 hectare = 2.4710538 acres (international acre)
_ACRES_PER_HECTARE = 2.4710538


def upgrade() -> None:
    """Upgrade schema."""
    # Backfill the imperial field from legacy metric values before dropping,
    # so no farm loses its only recorded area.
    op.execute(
        f"""
        UPDATE farms
        SET acreage_acres = ROUND(area_hectares * {_ACRES_PER_HECTARE}, 2)
        WHERE acreage_acres IS NULL AND area_hectares IS NOT NULL
        """
    )
    op.drop_column('farms', 'area_hectares')


def downgrade() -> None:
    """Downgrade schema."""
    # Restores the column only; original hectare values are not recoverable.
    op.add_column('farms', sa.Column('area_hectares', sa.Numeric(precision=10, scale=2), nullable=True))
