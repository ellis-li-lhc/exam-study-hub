"""Preserve admission plan fees, teaching sites and sourced institution facts."""
from alembic import op
import sqlalchemy as sa

revision = "d7a63e91b204"
down_revision = "c52f8a6d9b31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("institutions", sa.Column("supplemental_data", sa.JSON(), nullable=True))
    for name, column_type in (
        ("study_form", sa.String(32)),
        ("teaching_site", sa.Text()),
        ("tuition_amount", sa.Integer()),
        ("tuition_unit", sa.String(32)),
        ("tuition_raw", sa.String(255)),
        ("enrollment_scope", sa.String(64)),
    ):
        op.add_column("admission_plans", sa.Column(name, column_type, nullable=True))


def downgrade():
    for name in ("enrollment_scope", "tuition_raw", "tuition_unit", "tuition_amount", "teaching_site", "study_form"):
        op.drop_column("admission_plans", name)
    op.drop_column("institutions", "supplemental_data")
