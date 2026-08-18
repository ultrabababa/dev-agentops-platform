"""Add exact linear sample trajectory persistence for L4.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluation_sample_trajectory_messages",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=255), nullable=False),
        sa.Column("repeat_index", sa.Integer(), nullable=False),
        sa.Column("message_index", sa.Integer(), nullable=False),
        sa.Column("message_role", sa.String(length=20), nullable=False),
        sa.Column("message_json", sa.Text(), nullable=False),
        sa.Column("message_sha256", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint(
            "run_id", "case_id", "repeat_index", "message_index"
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "case_id", "repeat_index"],
            [
                "evaluation_sample_outcomes.run_id",
                "evaluation_sample_outcomes.case_id",
                "evaluation_sample_outcomes.repeat_index",
            ],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "repeat_index >= 0", name="ck_trajectory_repeat_index"
        ),
        sa.CheckConstraint(
            "message_index >= 0", name="ck_trajectory_message_index"
        ),
        sa.CheckConstraint(
            "message_role IN ('user', 'assistant', 'tool_result')",
            name="ck_trajectory_message_role",
        ),
    )
    op.execute(
        "UPDATE devagentops_metadata SET value = '6' WHERE key = 'schema_version'"
    )


def downgrade() -> None:
    op.drop_table("evaluation_sample_trajectory_messages")
    op.execute(
        "UPDATE devagentops_metadata SET value = '5' WHERE key = 'schema_version'"
    )
