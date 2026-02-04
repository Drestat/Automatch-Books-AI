"""add vendors table

Revision ID: add_vendors_table
Revises: add_payee_column
Create Date: 2026-02-04 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_vendors_table'
down_revision = 'add_payee_column'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('vendors',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('realm_id', sa.String(), nullable=True),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['realm_id'], ['qbo_connections.realm_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendors_realm_id'), 'vendors', ['realm_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_vendors_realm_id'), table_name='vendors')
    op.drop_table('vendors')
