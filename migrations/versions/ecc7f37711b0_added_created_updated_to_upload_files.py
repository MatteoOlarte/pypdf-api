"""added_created_updated_to_upload_files

Revision ID: ecc7f37711b0
Revises: 12cf0b9e505f
Create Date: 2024-11-22 21:35:02.854331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecc7f37711b0'
down_revision: Union[str, None] = '12cf0b9e505f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'upload_files',
        sa.Column('created', sa.DateTime(), nullable=True, server_default=sa.text('"2024-1-1 0:0:0"'))
    )
    op.add_column(
        'upload_files',
        sa.Column('updated', sa.DateTime(), nullable=True, server_default=sa.text('"2024-1-1 0:0:0"'))
    )


def downgrade() -> None:
    op.drop_column('upload_files', 'updated')
    op.drop_column('upload_files', 'created')
