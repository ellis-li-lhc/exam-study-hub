"""add password reset codes

Revision ID: 6e2c8e1d4b7f
Revises: c84c3d71a9f2
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6e2c8e1d4b7f"
down_revision: Union[str, Sequence[str], None] = "c84c3d71a9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_digest", sa.String(length=64), nullable=False),
        sa.Column("request_ip", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_reset_codes_email"), "password_reset_codes", ["email"])
    op.create_index(op.f("ix_password_reset_codes_request_ip"), "password_reset_codes", ["request_ip"])
    op.create_index(op.f("ix_password_reset_codes_created_at"), "password_reset_codes", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_password_reset_codes_created_at"), table_name="password_reset_codes")
    op.drop_index(op.f("ix_password_reset_codes_request_ip"), table_name="password_reset_codes")
    op.drop_index(op.f("ix_password_reset_codes_email"), table_name="password_reset_codes")
    op.drop_table("password_reset_codes")
