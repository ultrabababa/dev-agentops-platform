"""Create the local storage metadata table.

Revision ID: 0001
Revises: None
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    metadata_table = op.create_table(
        "devagentops_metadata",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=255), nullable=False),
    )
    op.bulk_insert(
        metadata_table,
        [{"key": "schema_version", "value": "1"}],
    )


def downgrade() -> None:
    op.drop_table("devagentops_metadata")
