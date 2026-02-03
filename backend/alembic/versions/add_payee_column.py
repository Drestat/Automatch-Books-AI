"""Add payee column to transactions

Revision ID: add_payee_column
Revises: bbe0bc5375a9
Create Date: 2026-02-03 10:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payee_column'
down_revision = 'c4f8e2a1b5d9'  # Points to add_is_bank_feed_import
branch_labels = None
depends_on = None


def upgrade():
    # Add payee column to transactions table
    op.add_column('transactions', sa.Column('payee', sa.String(), nullable=True))


def downgrade():
    # Remove payee column from transactions table
    op.drop_column('transactions', 'payee')
