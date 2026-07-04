"""add user state sync version

Revision ID: 5c4cfdc6e8aa
Revises: 9a6dfd3db62c
Create Date: 2026-07-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5c4cfdc6e8aa"
down_revision: Union[str, Sequence[str], None] = "9a6dfd3db62c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_states",
        sa.Column("sync_version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user_states", "sync_version")
