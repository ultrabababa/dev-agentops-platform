"""Create the Issue #16 evaluation run persistence slice.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("run_id", sa.String(length=36), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("condition_id", sa.String(length=255), nullable=False),
        sa.Column("runtime_variant", sa.String(length=100), nullable=False),
        sa.Column("suite_id", sa.String(length=255), nullable=False),
        sa.Column("suite_version", sa.String(length=100), nullable=False),
        sa.Column("condition_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("code_revision", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.String(length=40), nullable=False),
        sa.Column("completed_at", sa.String(length=40), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('finalizing', 'completed', 'failed')",
            name="ck_evaluation_runs_status",
        ),
    )
    op.create_table(
        "evaluation_run_manifests",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("manifest_sha256", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "evaluation_trace_events",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("case_id", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.String(length=40), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "sequence"),
    )
    op.create_table(
        "evaluation_reports",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("valid", sa.Boolean(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("validation_json", sa.Text(), nullable=False),
        sa.Column("report_sha256", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "case_id"),
    )
    op.create_table(
        "evaluation_case_scores",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("evaluation_method", sa.String(length=255), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("diagnostics_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "case_id"),
    )
    op.execute(
        "UPDATE devagentops_metadata SET value = '2' WHERE key = 'schema_version'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE devagentops_metadata SET value = '1' WHERE key = 'schema_version'"
    )
    op.drop_table("evaluation_case_scores")
    op.drop_table("evaluation_reports")
    op.drop_table("evaluation_trace_events")
    op.drop_table("evaluation_run_manifests")
    op.drop_table("evaluation_runs")
