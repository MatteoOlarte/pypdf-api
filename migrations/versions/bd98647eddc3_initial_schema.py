"""initial_schema

Revision ID: bd98647eddc3
Revises: 
Create Date: 2024-11-18 23:09:59.168282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bd98647eddc3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('pk', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('pk')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
