"""add alerts table and user phone fields

Revision ID: 5c8e2f7a91d4
Revises: 144332bd2033
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5c8e2f7a91d4'
down_revision: Union[str, Sequence[str], None] = '144332bd2033'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('sms_alerts_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)

    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        # stressseverity already exists — reference it without re-creating
        sa.Column('severity', postgresql.ENUM('green', 'yellow', 'red', name='stressseverity', create_type=False), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('days_to_stress', sa.Integer(), nullable=True),
        sa.Column('channel', sa.Enum('sms', name='alertchannel'), server_default='sms', nullable=False),
        sa.Column('provider_message_sid', sa.String(length=64), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('feedback', sa.Enum('yes', 'no', name='alertfeedback'), nullable=True),
        sa.Column('feedback_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_id', 'as_of_date', 'severity', name='uq_alert_farm_date_severity'),
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index(op.f('ix_alerts_farm_id'), 'alerts', ['farm_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_alerts_farm_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_id'), table_name='alerts')
    op.drop_table('alerts')
    sa.Enum(name='alertchannel').drop(op.get_bind())
    sa.Enum(name='alertfeedback').drop(op.get_bind())
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_column('users', 'sms_alerts_enabled')
    op.drop_column('users', 'phone_number')
