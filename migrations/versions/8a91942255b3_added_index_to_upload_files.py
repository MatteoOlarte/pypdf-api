"""added_index_to_upload_files

Revision ID: 8a91942255b3
Revises: ecc7f37711b0
Create Date: 2024-11-22 21:59:56.675685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a91942255b3'
down_revision: Union[str, None] = 'ecc7f37711b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_file_path', 'upload_files', ['path'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_file_path', table_name='upload_files')