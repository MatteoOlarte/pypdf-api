"""added_content_type_to_upload_files

Revision ID: 12cf0b9e505f
Revises: 4298c0ca046f
Create Date: 2024-11-22 21:23:14.398945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12cf0b9e505f'
down_revision: Union[str, None] = '4298c0ca046f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('upload_files', sa.Column('content_type', sa.String(length=100), nullable=False))


def downgrade() -> None:
    op.drop_column('upload_files', 'content_type')
