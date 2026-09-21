"""add seller_type to listings

Revision ID: 76cac0b39198
Revises: 577a6294a50e
Create Date: 2026-09-21 14:57:37.255754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76cac0b39198'
down_revision: Union[str, Sequence[str], None] = '577a6294a50e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('listings', sa.Column('seller_type', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('listings', 'seller_type')
