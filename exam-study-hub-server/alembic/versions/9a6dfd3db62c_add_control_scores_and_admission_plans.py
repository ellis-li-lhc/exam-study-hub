"""add control scores and admission plans

Revision ID: 9a6dfd3db62c
Revises: 417dc5f6fd03
Create Date: 2026-07-02 20:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a6dfd3db62c"
down_revision: Union[str, Sequence[str], None] = "417dc5f6fd03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("admission_scores", sa.Column("round", sa.String(length=64), nullable=True))

    op.create_table(
        "admission_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("major_code", sa.String(length=32), nullable=False),
        sa.Column("major_name", sa.String(length=128), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("category_code", sa.String(length=16), nullable=True),
        sa.Column("category_name", sa.String(length=64), nullable=True),
        sa.Column("plan_count", sa.Integer(), nullable=True),
        sa.Column("line_type", sa.String(length=32), nullable=False),
        sa.Column("round", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "institution_id", "year", "major_code", "line_type", "round",
            name="uq_admission_plan_inst_year_major_round",
        ),
    )
    op.create_index(op.f("ix_admission_plans_institution_id"), "admission_plans", ["institution_id"], unique=False)
    op.create_index(op.f("ix_admission_plans_major_code"), "admission_plans", ["major_code"], unique=False)
    op.create_index(op.f("ix_admission_plans_major_name"), "admission_plans", ["major_name"], unique=False)

    op.create_table(
        "province_control_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("province_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("category_code", sa.String(length=16), nullable=True),
        sa.Column("category_name", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("line_type", sa.String(length=32), nullable=False),
        sa.Column("round", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["province_id"], ["provinces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "province_id", "year", "level", "category_name", "line_type", "round",
            name="uq_province_control_score_year_category_round",
        ),
    )
    op.create_index(op.f("ix_province_control_scores_province_id"), "province_control_scores", ["province_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_province_control_scores_province_id"), table_name="province_control_scores")
    op.drop_table("province_control_scores")
    op.drop_index(op.f("ix_admission_plans_major_name"), table_name="admission_plans")
    op.drop_index(op.f("ix_admission_plans_major_code"), table_name="admission_plans")
    op.drop_index(op.f("ix_admission_plans_institution_id"), table_name="admission_plans")
    op.drop_table("admission_plans")
    op.drop_column("admission_scores", "round")
