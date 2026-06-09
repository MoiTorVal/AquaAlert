"""add job_runs table

Revision ID: c3f1a9d2e5b7
Revises: 09afc8407763
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f1a9d2e5b7'
down_revision: Union[str, Sequence[str], None] = '09afc8407763'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'job_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(length=100), nullable=False),
        sa.Column(
            'status',
            sa.Enum('running', 'success', 'failed', name='jobstatus'),
            server_default='running',
            nullable=False,
        ),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('farms_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('farms_failed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('farms_skipped', sa.Integer(), server_default='0', nullable=False),
        sa.Column('detail', sa.String(length=2000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_job_runs_id'), 'job_runs', ['id'], unique=False)
    op.create_index(op.f('ix_job_runs_job_name'), 'job_runs', ['job_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_job_runs_job_name'), table_name='job_runs')
    op.drop_index(op.f('ix_job_runs_id'), table_name='job_runs')
    op.drop_table('job_runs')
    sa.Enum(name='jobstatus').drop(op.get_bind())
