"""Add satellite scans table

Revision ID: 8f1d2c3b4a5e
Revises: b3f7c2d94a18
Create Date: 2026-06-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f1d2c3b4a5e'
down_revision: Union[str, Sequence[str], None] = 'b3f7c2d94a18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "satellite_scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farm_id", sa.Integer(), nullable=False),
        sa.Column("scan_date", sa.Date(), nullable=False),
        sa.Column("cloud_cover_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("mean_ndvi", sa.Numeric(4, 3), nullable=True),
        sa.Column("max_ndvi", sa.Numeric(4, 3), nullable=True),
        sa.Column("min_ndvi", sa.Numeric(4, 3), nullable=True),
        sa.Column("ndvi_grid", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ndvi_grid_bounds", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farm_id", "scan_date", name="uq_satscan_farm_date"),
    )
    op.create_index(op.f("ix_satellite_scans_id"), "satellite_scans", ["id"], unique=False)
    op.create_index(op.f("ix_satellite_scans_farm_id"), "satellite_scans", ["farm_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_satellite_scans_farm_id"), table_name="satellite_scans")
    op.drop_index(op.f("ix_satellite_scans_id"), table_name="satellite_scans")
    op.drop_table("satellite_scans")
