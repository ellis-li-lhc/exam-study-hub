"""preserve issue resolutions on user delete

Revision ID: c52f8a6d9b31
Revises: b31e7d4c5f12
Create Date: 2026-08-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c52f8a6d9b31"
down_revision: Union[str, Sequence[str], None] = "b31e7d4c5f12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("data_issue_resolutions_updated_by_user_id_fkey", "data_issue_resolutions", type_="foreignkey")
    op.alter_column("data_issue_resolutions", "updated_by_user_id", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key(
        "data_issue_resolutions_updated_by_user_id_fkey",
        "data_issue_resolutions",
        "users",
        ["updated_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("data_issue_resolutions_updated_by_user_id_fkey", "data_issue_resolutions", type_="foreignkey")
    op.alter_column("data_issue_resolutions", "updated_by_user_id", existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        "data_issue_resolutions_updated_by_user_id_fkey",
        "data_issue_resolutions",
        "users",
        ["updated_by_user_id"],
        ["id"],
    )
