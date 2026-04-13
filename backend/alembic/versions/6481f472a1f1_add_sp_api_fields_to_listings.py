"""add sp_api fields to listings

Revision ID: 6481f472a1f1
Revises: aa2b75bb7950
Create Date: 2026-04-13 23:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6481f472a1f1'
down_revision: Union[str, None] = 'aa2b75bb7950'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('listings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sp_api_submission_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sp_api_status', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('sp_api_last_polled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('listings', schema=None) as batch_op:
        batch_op.drop_column('sp_api_last_polled_at')
        batch_op.drop_column('sp_api_status')
        batch_op.drop_column('sp_api_submission_id')
