"""add frozen document indexes

Revision ID: 20260514_03
Revises: 20260514_02
Create Date: 2026-05-14
"""

from __future__ import annotations

from alembic import op


revision = "20260514_03"
down_revision = "20260514_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
    op.create_index("ix_tasks_building_code_status", "tasks", ["building_code", "status"])
    op.create_index("ix_transactions_wallet_id_created_at", "transactions", ["wallet_id", "created_at"])
    op.create_index(
        "ix_recommendation_snapshots_user_id_snapshot_date",
        "recommendation_snapshots",
        ["user_id", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_snapshots_user_id_snapshot_date", table_name="recommendation_snapshots")
    op.drop_index("ix_transactions_wallet_id_created_at", table_name="transactions")
    op.drop_index("ix_tasks_building_code_status", table_name="tasks")
    op.drop_index("ix_tasks_status_created_at", table_name="tasks")
