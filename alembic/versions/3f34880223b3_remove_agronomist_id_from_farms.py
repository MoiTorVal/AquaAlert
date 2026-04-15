"""remove agronomist_id from farms

Revision ID: 3f34880223b3
Revises: 92ed82f92c93
Create Date: 2026-04-13 21:16:44.802143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f34880223b3'
down_revision: Union[str, Sequence[str], None] = '92ed82f92c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:        
    op.drop_constraint("farms_agronomist_id_fkey", "farms", type_="foreignkey")
    op.drop_column("farms", "agronomist_id")                                                                     
   
def downgrade() -> None:                                                                       
    op.add_column("farms", sa.Column("agronomist_id", sa.Integer(), nullable=False))
    op.create_foreign_key("farms_agronomist_id_fkey", "farms", "agronomists", ["agronomist_id"], ["id"]) 