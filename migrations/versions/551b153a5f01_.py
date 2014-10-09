"""empty message

Revision ID: 551b153a5f01
Revises: None
Create Date: 2014-10-09 11:26:28.297994

"""

# revision identifiers, used by Alembic.
revision = '551b153a5f01'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group_metadata',
    sa.Column('ct_id', sa.Integer(), nullable=False),
    sa.Column('image', sa.String(length=120), nullable=True),
    sa.Column('description', sa.String(length=700), nullable=True),
    sa.PrimaryKeyConstraint('ct_id'),
    sa.UniqueConstraint('ct_id')
    )
    op.create_table('news',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=120), nullable=True),
    sa.Column('body', sa.String(length=700), nullable=True),
    sa.Column('pub_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('news')
    op.drop_table('group_metadata')
    ### end Alembic commands ###
