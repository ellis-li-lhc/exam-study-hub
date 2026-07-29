"""add email verification

Revision ID: c84c3d71a9f2
Revises: 5c4cfdc6e8aa
Create Date: 2026-07-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c84c3d71a9f2"
down_revision: Union[str, Sequence[str], None] = "5c4cfdc6e8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "email_verification_codes",
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
    op.create_index(op.f("ix_email_verification_codes_email"), "email_verification_codes", ["email"])
    op.create_index(op.f("ix_email_verification_codes_request_ip"), "email_verification_codes", ["request_ip"])
    op.create_index(op.f("ix_email_verification_codes_created_at"), "email_verification_codes", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verification_codes_created_at"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_request_ip"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_email"), table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
    op.drop_column("users", "email_verified_at")
