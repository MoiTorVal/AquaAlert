"""Cascade-delete farm child rows

Deleting a farm previously raised IntegrityError once any child rows
(ET readings, sim outputs, events, baselines, savings) existed.

Revision ID: f4a8d1c92e37
Revises: d8e2f4a1b6c9
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f4a8d1c92e37'
down_revision: Union[str, Sequence[str], None] = 'd8e2f4a1b6c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Every table holding a farm_id FK. Constraint names are Postgres defaults
# (<table>_<column>_fkey) because the original migrations left them unnamed.
FARM_CHILD_TABLES = (
    "weather_readings",
    "et_readings",
    "aquacrop_outputs",
    "irrigation_events",
    "baseline_irrigations",
    "water_savings",
)


def _recreate_fks(ondelete: Union[str, None]) -> None:
    for table in FARM_CHILD_TABLES:
        constraint = f"{table}_farm_id_fkey"
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.create_foreign_key(
            constraint, table, "farms", ["farm_id"], ["id"], ondelete=ondelete
        )


def upgrade() -> None:
    _recreate_fks("CASCADE")


def downgrade() -> None:
    _recreate_fks(None)
