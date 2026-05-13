"""phase1 schema additions: timestamps tzaware, aquacrop outputs, irrigation events, water savings, user profile fields

Revision ID: a7c4e9f12b80
Revises: e61ce02beb20
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7c4e9f12b80'
down_revision: Union[str, Sequence[str], None] = 'e61ce02beb20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'aquacrop_outputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('run_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('depletion_mm', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('root_zone_moisture_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('severity', sa.Enum('green', 'yellow', 'red', name='stressseverity'), nullable=True),
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

    op.execute("CREATE TYPE locale AS ENUM ('en', 'es')")
    op.execute("CREATE TYPE tier AS ENUM ('free', 'paid')")
    op.execute("CREATE TYPE irrigationsource AS ENUM ('user_log', 'estimated')")
    op.execute("CREATE TYPE watersource AS ENUM ('well', 'canal', 'surface')")

    op.add_column(
        'users',
        sa.Column(
            'locale',
            postgresql.ENUM('en', 'es', name='locale', create_type=False),
            nullable=False,
            server_default='en',
        ),
    )
    op.add_column('users', sa.Column('is_socially_disadvantaged', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('is_beginning_farmer', sa.Boolean(), nullable=True))
    op.add_column(
        'users',
        sa.Column(
            'tier',
            postgresql.ENUM('free', 'paid', name='tier', create_type=False),
            nullable=False,
            server_default='free',
        ),
    )

    op.add_column('farms', sa.Column('acreage_acres', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('farms', sa.Column('pump_hp', sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column('farms', sa.Column('pump_lift_ft', sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column(
        'farms',
        sa.Column(
            'water_source',
            postgresql.ENUM('well', 'canal', 'surface', name='watersource', create_type=False),
            nullable=True,
        ),
    )

    op.create_table(
        'irrigation_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('gallons_applied', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            'source',
            postgresql.ENUM('user_log', 'estimated', name='irrigationsource', create_type=False),
            nullable=False,
        ),
        sa.Column(
            'logged_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_irrigation_events_id'), 'irrigation_events', ['id'], unique=False)

    op.create_table(
        'water_savings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('baseline_gallons', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('actual_gallons', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('gallons_saved', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('kwh_saved', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('co2_kg_saved', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            'computed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_id', 'period_start', 'period_end', name='uq_water_savings_farm_period'),
    )
    op.create_index(op.f('ix_water_savings_id'), 'water_savings', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_water_savings_id'), table_name='water_savings')
    op.drop_table('water_savings')

    op.drop_index(op.f('ix_irrigation_events_id'), table_name='irrigation_events')
    op.drop_table('irrigation_events')

    op.drop_column('farms', 'water_source')
    op.drop_column('farms', 'pump_lift_ft')
    op.drop_column('farms', 'pump_hp')
    op.drop_column('farms', 'acreage_acres')

    op.drop_column('users', 'tier')
    op.drop_column('users', 'is_beginning_farmer')
    op.drop_column('users', 'is_socially_disadvantaged')
    op.drop_column('users', 'locale')

    op.execute("DROP TYPE watersource")
    op.execute("DROP TYPE irrigationsource")
    op.execute("DROP TYPE tier")
    op.execute("DROP TYPE locale")

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
