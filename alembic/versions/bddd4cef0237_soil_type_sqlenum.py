"""soil_type_sqlenum

Revision ID: bddd4cef0237
Revises: 72a69b474d25
Create Date: 2026-05-03 21:23:29.496404

"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bddd4cef0237'
down_revision: Union[str, Sequence[str], None] = '72a69b474d25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:    
    op.add_column('farms', sa.Column('field_polygon', geoalchemy2.types.Geometry(geometry_type='POLYGON',
srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True))                           
    op.add_column('farms', sa.Column('harvest_date', sa.Date(), nullable=True))
    sa.Enum('Sandy', 'LoamySand', 'SandyLoam', 'Loam', 'SiltLoam', 'Silt', 'SandyClayLoam', 'ClayLoam',
  'SiltyClayLoam', 'SandyClay', 'SiltyClay', 'Clay', name='soiltexture').create(op.get_bind())
    op.alter_column('farms', 'soil_type',              
                existing_type=sa.VARCHAR(length=100),   
                type_=sa.Enum('Sandy', 'LoamySand', 'SandyLoam', 'Loam', 'SiltLoam', 'Silt', 'SandyClayLoam',
'ClayLoam', 'SiltyClayLoam', 'SandyClay', 'SiltyClay', 'Clay', name='soiltexture'),                              
                existing_nullable=True, postgresql_using='soil_type::soiltexture')                 
    op.create_index('idx_farms_field_polygon', 'farms', ['field_polygon'], unique=False, postgresql_using='gist', if_not_exists=True)



def downgrade() -> None:  
    op.drop_index('idx_farms_field_polygon', table_name='farms', postgresql_using='gist')                        
    op.alter_column('farms', 'soil_type',              
                existing_type=sa.Enum('Sandy', 'LoamySand', 'SandyLoam', 'Loam', 'SiltLoam', 'Silt',
'SandyClayLoam', 'ClayLoam', 'SiltyClayLoam', 'SandyClay', 'SiltyClay', 'Clay', name='soiltexture', ),             
                type_=sa.VARCHAR(length=100),
                existing_nullable=True, postgresql_using='soil_type::soiltexture')  
    sa.Enum(name='soiltexture').drop(op.get_bind())               
    op.drop_column('farms', 'harvest_date')            
    op.drop_column('farms', 'field_polygon')