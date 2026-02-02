"""add_is_bank_feed_import_to_transactions

Revision ID: c4f8e2a1b5d9
Revises: bbe0bc5375a9
Create Date: 2026-02-02 15:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f8e2a1b5d9'
down_revision: Union[str, Sequence[str], None] = 'bbe0bc5375a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_bank_feed_import column to transactions table."""
    op.add_column('transactions', sa.Column('is_bank_feed_import', sa.Boolean(), nullable=True, server_default='true'))
    # Set default to True for existing transactions (assume bank feed unless TxnType=54)
    op.execute("UPDATE transactions SET is_bank_feed_import = true WHERE is_bank_feed_import IS NULL")


def downgrade() -> None:
    """Remove is_bank_feed_import column from transactions table."""
    op.drop_column('transactions', 'is_bank_feed_import')
