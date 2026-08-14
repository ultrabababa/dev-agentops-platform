"""Add repeated-sample persistence for the Issue #41 execution engine.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.drop_constraint("ck_evaluation_runs_status", type_="check")
        batch_op.create_check_constraint(
            "ck_evaluation_runs_status",
            "status IN ('finalizing', 'completed', "
            "'completed_with_case_failures', "
            "'completed_with_sample_failures', 'failed')",
        )

    with op.batch_alter_table("evaluation_trace_events") as batch_op:
        batch_op.add_column(sa.Column("repeat_index", sa.Integer(), nullable=True))

    op.create_table(
        "evaluation_sample_outcomes",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("repeat_index", sa.Integer(), nullable=False),
        sa.Column("sample_sequence", sa.Integer(), nullable=False),
        sa.Column("suite_weight", sa.Float(), nullable=False),
        sa.Column("evaluation_failure_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_stage", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "case_id", "repeat_index"),
        sa.UniqueConstraint("run_id", "sample_sequence"),
        sa.CheckConstraint(
            "repeat_index >= 0",
            name="ck_sample_outcomes_repeat_index",
        ),
        sa.CheckConstraint(
            "sample_sequence >= 1",
            name="ck_sample_outcomes_sequence",
        ),
        sa.CheckConstraint(
            "suite_weight > 0",
            name="ck_sample_outcomes_weight",
        ),
        sa.CheckConstraint(
            "status IN ('scored', 'execution_failed')",
            name="ck_sample_outcomes_status",
        ),
        sa.CheckConstraint(
            "(status = 'scored' AND failure_code IS NULL "
            "AND failure_stage IS NULL AND failure_message IS NULL) OR "
            "(status = 'execution_failed' AND failure_code IS NOT NULL "
            "AND failure_stage IS NOT NULL AND failure_message IS NOT NULL)",
            name="ck_sample_outcomes_failure_shape",
        ),
    )
    op.create_table(
        "evaluation_sample_reports",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("repeat_index", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("valid", sa.Boolean(), nullable=False),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("validation_json", sa.Text(), nullable=False),
        sa.Column("report_sha256", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "case_id", "repeat_index"),
    )
    op.create_table(
        "evaluation_sample_scores",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("repeat_index", sa.Integer(), nullable=False),
        sa.Column("evaluation_method", sa.String(length=255), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("diagnostics_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "case_id", "repeat_index"),
    )
    op.execute(
        "UPDATE devagentops_metadata SET value = '4' WHERE key = 'schema_version'"
    )


def downgrade() -> None:
    op.drop_table("evaluation_sample_scores")
    op.drop_table("evaluation_sample_reports")
    op.drop_table("evaluation_sample_outcomes")

    op.execute(
        "UPDATE evaluation_runs SET status = 'failed' "
        "WHERE status = 'completed_with_sample_failures'"
    )
    with op.batch_alter_table("evaluation_trace_events") as batch_op:
        batch_op.drop_column("repeat_index")
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.drop_constraint("ck_evaluation_runs_status", type_="check")
        batch_op.create_check_constraint(
            "ck_evaluation_runs_status",
            "status IN ('finalizing', 'completed', "
            "'completed_with_case_failures', 'failed')",
        )
    op.execute(
        "UPDATE devagentops_metadata SET value = '3' WHERE key = 'schema_version'"
    )
