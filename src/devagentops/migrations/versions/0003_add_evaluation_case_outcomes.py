"""Add queryable per-Case outcomes for Issue #35 Debug Runs.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.drop_constraint("ck_evaluation_runs_status", type_="check")
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            type_=sa.String(length=40),
            existing_nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_evaluation_runs_status",
            "status IN ('finalizing', 'completed', "
            "'completed_with_case_failures', 'failed')",
        )
    op.create_table(
        "evaluation_case_outcomes",
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("suite_weight", sa.Float(), nullable=False),
        sa.Column("evaluation_failure_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_stage", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "case_id"),
        sa.UniqueConstraint("run_id", "sequence"),
        sa.CheckConstraint("sequence >= 1", name="ck_case_outcomes_sequence"),
        sa.CheckConstraint("suite_weight > 0", name="ck_case_outcomes_weight"),
        sa.CheckConstraint(
            "status IN ('scored', 'execution_failed')",
            name="ck_case_outcomes_status",
        ),
        sa.CheckConstraint(
            "(status = 'scored' AND failure_code IS NULL "
            "AND failure_stage IS NULL AND failure_message IS NULL) OR "
            "(status = 'execution_failed' AND failure_code IS NOT NULL "
            "AND failure_stage IS NOT NULL AND failure_message IS NOT NULL)",
            name="ck_case_outcomes_failure_shape",
        ),
    )
    op.execute(
        "UPDATE devagentops_metadata SET value = '3' WHERE key = 'schema_version'"
    )


def downgrade() -> None:
    op.drop_table("evaluation_case_outcomes")
    op.execute(
        "UPDATE evaluation_runs SET status = 'failed' "
        "WHERE status = 'completed_with_case_failures'"
    )
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.drop_constraint("ck_evaluation_runs_status", type_="check")
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=40),
            type_=sa.String(length=20),
            existing_nullable=False,
        )
        batch_op.create_check_constraint(
            "ck_evaluation_runs_status",
            "status IN ('finalizing', 'completed', 'failed')",
        )
    op.execute(
        "UPDATE devagentops_metadata SET value = '2' WHERE key = 'schema_version'"
    )
