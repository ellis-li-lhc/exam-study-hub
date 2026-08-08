"""add password version to users

Revision ID: 8b7d2e4c1f90
Revises: 6e2c8e1d4b7f
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b7d2e4c1f90"
down_revision: Union[str, Sequence[str], None] = "6e2c8e1d4b7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_version", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "password_version")
