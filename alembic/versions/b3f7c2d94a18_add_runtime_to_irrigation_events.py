"""Add pump-runtime fields to irrigation events

Runtime-mode logs previously collapsed to gallons client-side, losing
the hours/GPM the farmer actually entered. Both columns are nullable —
gallons-mode logs never set them.

Revision ID: b3f7c2d94a18
Revises: 5c8e2f7a91d4
Create Date: 2026-06-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3f7c2d94a18'
down_revision: Union[str, Sequence[str], None] = '5c8e2f7a91d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "irrigation_events",
        sa.Column("hours_run", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "irrigation_events",
        sa.Column("pump_gpm", sa.Numeric(8, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("irrigation_events", "pump_gpm")
    op.drop_column("irrigation_events", "hours_run")
