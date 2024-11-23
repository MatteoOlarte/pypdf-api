"""added_file_2

Revision ID: 4298c0ca046f
Revises: bd98647eddc3
Create Date: 2024-11-19 17:52:21.786827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4298c0ca046f'
down_revision: Union[str, None] = 'bd98647eddc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('upload_files',
        sa.Column('pk', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=250), nullable=False),
        sa.Column('extension', sa.String(length=100), nullable=False),
        sa.Column('path', sa.String(length=250), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.pk'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('pk')
    )
    op.create_index('idx_file_name', 'upload_files', ['name', 'extension'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_file_name', table_name='upload_files')
    op.drop_table('upload_files')
