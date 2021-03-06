"""empty message

Revision ID: 3660fb105f1
Revises: 4e6f542c9d30
Create Date: 2015-03-18 11:29:39.067214

"""

# revision identifiers, used by Alembic.
revision = '3660fb105f1'
down_revision = '4e6f542c9d30'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('whatsup_upvotes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['whatsup.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user_metadata.ct_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('whatsup_upvotes')
    ### end Alembic commands ###
