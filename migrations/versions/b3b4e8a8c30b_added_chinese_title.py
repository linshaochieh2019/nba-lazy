"""Added chinese_title

Revision ID: b3b4e8a8c30b
Revises: f6d92d99cedc
Create Date: 2023-11-11 15:24:41.676243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3b4e8a8c30b'
down_revision = 'f6d92d99cedc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('chinese_title', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_column('chinese_title')

    # ### end Alembic commands ###
