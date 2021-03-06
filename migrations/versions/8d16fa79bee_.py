"""empty message

Revision ID: 8d16fa79bee
Revises: 3e5360da8368
Create Date: 2015-04-28 11:27:02.118964

"""

# revision identifiers, used by Alembic.
revision = '8d16fa79bee'
down_revision = '3e5360da8368'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prayers', sa.Column('name', sa.String(length=120), nullable=True))
    op.drop_column('prayers', 'show_user')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prayers', sa.Column('show_user', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('prayers', 'name')
    ### end Alembic commands ###
