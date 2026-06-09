"""add regional_stats table

Revision ID: d8e2f4a1b6c9
Revises: c3f1a9d2e5b7
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8e2f4a1b6c9'
down_revision: Union[str, Sequence[str], None] = 'c3f1a9d2e5b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'regional_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_farms', sa.Integer(), nullable=False),
        sa.Column('farms_green', sa.Integer(), nullable=False),
        sa.Column('farms_yellow', sa.Integer(), nullable=False),
        sa.Column('farms_red', sa.Integer(), nullable=False),
        sa.Column('total_gallons_saved', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_kwh_saved', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_co2_kg_saved', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_date'),
    )
    op.create_index(op.f('ix_regional_stats_id'), 'regional_stats', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_regional_stats_id'), table_name='regional_stats')
    op.drop_table('regional_stats')
