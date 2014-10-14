"""empty message

Revision ID: 33412106cdda
Revises: 1b9ea55dce82
Create Date: 2014-10-13 13:09:06.168221

"""

# revision identifiers, used by Alembic.
revision = '33412106cdda'
down_revision = '1b9ea55dce82'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('image_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'images', sa.Column('category_id', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'images', 'category_id')
    op.drop_table('image_category')
    ### end Alembic commands ###
