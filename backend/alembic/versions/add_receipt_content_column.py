"""add receipt_content column

Revision ID: add_receipt_content
Revises: 1cbc05e8f2b4
Create Date: 2026-02-07 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_receipt_content'
down_revision = '1cbc05e8f2b4'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('transactions', sa.Column('receipt_content', sa.LargeBinary(), nullable=True))

def downgrade():
    op.drop_column('transactions', 'receipt_content')
