"""entry table

Revision ID: 2a534d70df8e
Revises: 
Create Date: 2023-03-16 23:20:44.440181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a534d70df8e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('entry__post',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('type', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(length=2048), nullable=True),
    sa.Column('test2summarize', sa.String(length=214748364), nullable=True),
    sa.Column('openAIsummary', sa.String(length=214748), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entry__post', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entry__post_openAIsummary'), ['openAIsummary'], unique=False)
        batch_op.create_index(batch_op.f('ix_entry__post_test2summarize'), ['test2summarize'], unique=False)
        batch_op.create_index(batch_op.f('ix_entry__post_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_entry__post_type'), ['type'], unique=False)
        batch_op.create_index(batch_op.f('ix_entry__post_url'), ['url'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entry__post', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entry__post_url'))
        batch_op.drop_index(batch_op.f('ix_entry__post_type'))
        batch_op.drop_index(batch_op.f('ix_entry__post_timestamp'))
        batch_op.drop_index(batch_op.f('ix_entry__post_test2summarize'))
        batch_op.drop_index(batch_op.f('ix_entry__post_openAIsummary'))

    op.drop_table('entry__post')
    # ### end Alembic commands ###