"""Add formal Case-first aggregate persistence.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _run_foreign_key() -> sa.ForeignKey:
    return sa.ForeignKey("evaluation_runs.run_id", ondelete="CASCADE")


def _coverage_columns(*, include_quality: bool) -> list[sa.Column]:
    columns = [
        sa.Column("requested_sample_count", sa.Integer(), nullable=False),
        sa.Column("scored_sample_count", sa.Integer(), nullable=False),
        sa.Column("execution_failed_sample_count", sa.Integer(), nullable=False),
        sa.Column("execution_coverage", sa.Float(), nullable=False),
        sa.Column("protocol_valid_sample_count", sa.Integer(), nullable=False),
        sa.Column("protocol_invalid_sample_count", sa.Integer(), nullable=False),
        sa.Column("protocol_validity_rate", sa.Float(), nullable=True),
    ]
    if include_quality:
        columns.extend(
            [
                sa.Column("cases_with_quality", sa.Integer(), nullable=False),
                sa.Column("cases_without_quality", sa.Integer(), nullable=False),
                sa.Column("quality_case_coverage", sa.Float(), nullable=False),
                sa.Column(
                    "quality_suite_weight_coverage", sa.Float(), nullable=False
                ),
            ]
        )
    return columns


def _quality_constraints(prefix: str) -> list[sa.CheckConstraint]:
    return [
        sa.CheckConstraint(
            "quality_status IN ('complete', 'incomplete')",
            name=f"ck_{prefix}_quality_status",
        ),
        sa.CheckConstraint(
            "(quality_status = 'complete' AND metrics_json IS NOT NULL) OR "
            "(quality_status = 'incomplete' AND metrics_json IS NULL)",
            name=f"ck_{prefix}_quality_shape",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "evaluation_case_aggregates",
        sa.Column("run_id", sa.String(length=36), _run_foreign_key(), nullable=False),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("case_sequence", sa.Integer(), nullable=False),
        sa.Column("case_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("failure_type", sa.String(length=100), nullable=False),
        sa.Column("suite_weight", sa.Float(), nullable=False),
        sa.Column("aggregation_method", sa.String(length=100), nullable=False),
        sa.Column("aggregation_version", sa.String(length=20), nullable=False),
        *_coverage_columns(include_quality=False),
        sa.Column("quality_status", sa.String(length=20), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("scored_repeat_indices_json", sa.Text(), nullable=False),
        sa.Column("failed_repeat_indices_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("run_id", "case_id"),
        sa.UniqueConstraint("run_id", "case_sequence"),
        sa.CheckConstraint("case_sequence >= 1", name="ck_case_aggregate_sequence"),
        sa.CheckConstraint("suite_weight > 0", name="ck_case_aggregate_weight"),
        *_quality_constraints("case_aggregate"),
    )
    op.create_table(
        "evaluation_suite_aggregates",
        sa.Column("run_id", sa.String(length=36), _run_foreign_key(), primary_key=True),
        sa.Column("suite_id", sa.String(length=255), nullable=False),
        sa.Column("suite_version", sa.String(length=100), nullable=False),
        sa.Column("suite_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("aggregation_method", sa.String(length=100), nullable=False),
        sa.Column("aggregation_version", sa.String(length=20), nullable=False),
        sa.Column("configured_suite_weight", sa.Float(), nullable=False),
        sa.Column("total_case_count", sa.Integer(), nullable=False),
        *_coverage_columns(include_quality=True),
        sa.Column("quality_status", sa.String(length=20), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        *_quality_constraints("suite_aggregate"),
    )
    op.create_table(
        "evaluation_failure_type_aggregates",
        sa.Column("run_id", sa.String(length=36), _run_foreign_key(), nullable=False),
        sa.Column("failure_type", sa.String(length=100), nullable=False),
        sa.Column("type_sequence", sa.Integer(), nullable=False),
        sa.Column("aggregation_method", sa.String(length=100), nullable=False),
        sa.Column("aggregation_version", sa.String(length=20), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("configured_suite_weight", sa.Float(), nullable=False),
        *_coverage_columns(include_quality=True),
        sa.Column("quality_status", sa.String(length=20), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "failure_type"),
        sa.UniqueConstraint("run_id", "type_sequence"),
        sa.CheckConstraint("type_sequence >= 1", name="ck_type_aggregate_sequence"),
        *_quality_constraints("failure_type_aggregate"),
    )
    op.execute(
        "UPDATE devagentops_metadata SET value = '5' WHERE key = 'schema_version'"
    )


def downgrade() -> None:
    op.drop_table("evaluation_failure_type_aggregates")
    op.drop_table("evaluation_suite_aggregates")
    op.drop_table("evaluation_case_aggregates")
    op.execute(
        "UPDATE devagentops_metadata SET value = '4' WHERE key = 'schema_version'"
    )
