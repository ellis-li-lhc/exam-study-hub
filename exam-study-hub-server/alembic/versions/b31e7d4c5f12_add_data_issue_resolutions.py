"""add data issue resolutions

Revision ID: b31e7d4c5f12
Revises: 8b7d2e4c1f90
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b31e7d4c5f12"
down_revision: Union[str, Sequence[str], None] = "8b7d2e4c1f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_issue_resolutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_key", sa.String(length=96), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_key"),
    )
    op.create_index(op.f("ix_data_issue_resolutions_issue_key"), "data_issue_resolutions", ["issue_key"])
    op.create_index(op.f("ix_data_issue_resolutions_updated_by_user_id"), "data_issue_resolutions", ["updated_by_user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_data_issue_resolutions_updated_by_user_id"), table_name="data_issue_resolutions")
    op.drop_index(op.f("ix_data_issue_resolutions_issue_key"), table_name="data_issue_resolutions")
    op.drop_table("data_issue_resolutions")
