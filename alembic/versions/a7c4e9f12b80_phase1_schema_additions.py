"""phase1 schema additions: irrigation events, water savings, user profile fields

Revision ID: a7c4e9f12b80
Revises: 33bd4f906ce2
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7c4e9f12b80'
down_revision: Union[str, Sequence[str], None] = '33bd4f906ce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE locale AS ENUM ('en', 'es')")
    op.execute("CREATE TYPE tier AS ENUM ('free', 'paid')")
    op.execute("CREATE TYPE irrigationsource AS ENUM ('user_log', 'estimated')")
    op.execute("CREATE TYPE watersource AS ENUM ('WELL', 'CANAL', 'SURFACE')")

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
            postgresql.ENUM('WELL', 'CANAL', 'SURFACE', name='watersource', create_type=False),
            nullable=True,
        ),
    )

    op.create_table(
        'baseline_irrigations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('gallons_per_week_estimate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('schedule_notes', sa.String(length=500), nullable=True),
        sa.Column(
            'captured_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_id', 'season_year', name='uq_baseline_farm_season'),
    )
    op.create_index(op.f('ix_baseline_irrigations_id'), 'baseline_irrigations', ['id'], unique=False)

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

    op.drop_index(op.f('ix_baseline_irrigations_id'), table_name='baseline_irrigations')
    op.drop_table('baseline_irrigations')

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
