"""enable postgis extension

Revision ID: 3e5e68d1976a
Revises:
Create Date: 2026-06-22

Base migration. PostGIS must exist before any geometry/geography column is
created, so this sits ahead of the original initial schema. The test image
(postgis/postgis) ships the extension pre-enabled, but a managed Postgres
(e.g. Railway) does not — without this, ``alembic upgrade head`` fails on the
first spatial column. CREATE/DROP ... IF [NOT] EXISTS keep it idempotent.

The database role running migrations must have CREATE EXTENSION privilege
(Railway's default Postgres role does).
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3e5e68d1976a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # Only reached on a full downgrade to base, by which point every spatial
    # table is already gone, so dropping the extension is safe.
    op.execute("DROP EXTENSION IF EXISTS postgis")
