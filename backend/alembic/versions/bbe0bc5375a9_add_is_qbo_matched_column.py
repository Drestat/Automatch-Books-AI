"""add_is_qbo_matched_column

Revision ID: bbe0bc5375a9
Revises: a8879455fdf3
Create Date: 2026-02-01 19:01:14.614405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbe0bc5375a9'
down_revision: Union[str, Sequence[str], None] = 'a8879455fdf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transactions', sa.Column('is_qbo_matched', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transactions', 'is_qbo_matched')
