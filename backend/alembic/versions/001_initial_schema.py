"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "appeals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("patient_name", sa.String(255), nullable=False, server_default="Unknown"),
        sa.Column("patient_dob", sa.String(20), nullable=False, server_default=""),
        sa.Column("member_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("insurance_company", sa.String(255), nullable=False, server_default=""),
        sa.Column("claim_number", sa.String(100), nullable=False, server_default=""),
        sa.Column("denial_date", sa.String(20), nullable=False, server_default=""),
        sa.Column("denial_reason", sa.Text, nullable=False),
        sa.Column("denied_service", sa.Text, nullable=False),
        sa.Column("cpt_codes", sa.String(255), nullable=False, server_default=""),
        sa.Column("icd10_codes", sa.String(255), nullable=False, server_default=""),
        sa.Column("physician_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("physician_npi", sa.String(20), nullable=False, server_default=""),
        sa.Column("practice_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("clinical_notes", sa.Text, nullable=False),
        sa.Column("parsed_clinical_data", sa.Text, nullable=True),
        sa.Column("generated_letter", sa.Text, nullable=True),
        sa.Column("citations", JSONB, nullable=True),
        sa.Column("rag_sources", JSONB, nullable=True),
        sa.Column("analysis_result", sa.Text, nullable=True),
        sa.CheckConstraint(
            "status IN ('draft','generating','completed','submitted','approved','denied','failed')",
            name="ck_appeals_status",
        ),
    )

    op.create_index("idx_appeals_created_at", "appeals", [sa.text("created_at DESC")])
    op.create_index("idx_appeals_status", "appeals", ["status"])


def downgrade() -> None:
    op.drop_table("appeals")
