"""timestamps tzaware + server defaults

Revision ID: 33bd4f906ce2
Revises: e61ce02beb20
Create Date: 2026-05-05 20:37:41.764561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '33bd4f906ce2'
down_revision: Union[str, Sequence[str], None] = 'e61ce02beb20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # New table — aquacrop sim outputs.
    op.create_table(
        'aquacrop_outputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('run_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('depletion_mm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('root_zone_moisture_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('severity', sa.Enum('GREEN', 'YELLOW', 'RED', name='stressseverity'), nullable=True),
        sa.Column('days_to_stress', sa.Integer(), nullable=True),
        sa.Column('paw_mm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('raw_threshold_mm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_id', 'as_of_date', name='uq_aquacrop_farm_date'),
    )
    op.create_index(op.f('ix_aquacrop_outputs_id'), 'aquacrop_outputs', ['id'], unique=False)

    # Backfill NULLs before flipping nullable=False.
    op.execute("UPDATE users SET created_at = now() WHERE created_at IS NULL")
    op.execute("UPDATE users SET password_changed_at = now() WHERE password_changed_at IS NULL")
    op.execute("UPDATE farms SET created_at = now() WHERE created_at IS NULL")

    # Type changes: TIMESTAMP → TIMESTAMPTZ.
    # postgresql_using interprets existing naive values as UTC (matches old app behavior:
    # `datetime.now(timezone.utc)` was written into tz-naive columns).
    op.alter_column(
        'users', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=sa.text('now()'),
        nullable=False,
    )
    op.alter_column(
        'users', 'password_changed_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="password_changed_at AT TIME ZONE 'UTC'",
        server_default=sa.text('now()'),
        nullable=False,
    )
    op.alter_column(
        'farms', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=sa.text('now()'),
        nullable=False,
    )
    op.alter_column(
        'password_reset_tokens', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=sa.text('now()'),
        existing_nullable=False,
    )
    op.alter_column(
        'password_reset_tokens', 'expires_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        'et_readings', 'fetched_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="fetched_at AT TIME ZONE 'UTC'",
        server_default=sa.text('now()'),
        existing_nullable=False,
    )
    op.alter_column(
        'weather_readings', 'recorded_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        postgresql_using="recorded_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'weather_readings', 'recorded_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="recorded_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        'et_readings', 'fetched_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="fetched_at AT TIME ZONE 'UTC'",
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        'password_reset_tokens', 'expires_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
        existing_nullable=False,
    )
    op.alter_column(
        'password_reset_tokens', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        'farms', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=None,
        nullable=True,
    )
    op.alter_column(
        'users', 'password_changed_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="password_changed_at AT TIME ZONE 'UTC'",
        server_default=None,
        nullable=True,
    )
    op.alter_column(
        'users', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        postgresql_using="created_at AT TIME ZONE 'UTC'",
        server_default=None,
        nullable=True,
    )

    op.drop_index(op.f('ix_aquacrop_outputs_id'), table_name='aquacrop_outputs')
    op.drop_table('aquacrop_outputs')