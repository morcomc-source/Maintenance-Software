"""Add part_transactions table

Revision ID: 330945c0af60
Revises: a00920c39834
Create Date: 2026-08-09 12:13:07.839382
"""
from alembic import op
import sqlalchemy as sa

revision = '330945c0af60'
down_revision = 'a00920c39834'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('part_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=80), nullable=True),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('part_transactions')
