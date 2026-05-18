"""add B core constraints and indexes

Revision ID: 20260518_000002
Revises: 20260415_000001
Create Date: 2026-05-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context, op


revision = "20260518_000002"
down_revision = "20260415_000001"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_constraints(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if context.is_offline_mode():
        op.create_unique_constraint(
            "uq_ratings_task_id_from_user_id",
            "ratings",
            ["task_id", "from_user_id"],
        )
        op.add_column("transactions", sa.Column("settlement_key", sa.String(length=25), nullable=True))
        op.create_unique_constraint(
            "uq_transactions_settlement_key",
            "transactions",
            ["settlement_key"],
        )
        op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
        op.create_index("ix_tasks_building_code_status", "tasks", ["building_code", "status"])
        op.create_index("ix_transactions_wallet_id_created_at", "transactions", ["wallet_id", "created_at"])
        op.create_index(
            "ix_recommendation_snapshots_user_id_snapshot_date",
            "recommendation_snapshots",
            ["user_id", "snapshot_date"],
        )
        return

    if "uq_ratings_task_id_from_user_id" not in _unique_constraints("ratings"):
        op.create_unique_constraint(
            "uq_ratings_task_id_from_user_id",
            "ratings",
            ["task_id", "from_user_id"],
        )

    if "settlement_key" not in _columns("transactions"):
        op.add_column("transactions", sa.Column("settlement_key", sa.String(length=25), nullable=True))
    if "uq_transactions_settlement_key" not in _unique_constraints("transactions"):
        op.create_unique_constraint(
            "uq_transactions_settlement_key",
            "transactions",
            ["settlement_key"],
        )

    task_indexes = _indexes("tasks")
    if "ix_tasks_status_created_at" not in task_indexes:
        op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
    if "ix_tasks_building_code_status" not in task_indexes:
        op.create_index("ix_tasks_building_code_status", "tasks", ["building_code", "status"])

    if "ix_transactions_wallet_id_created_at" not in _indexes("transactions"):
        op.create_index("ix_transactions_wallet_id_created_at", "transactions", ["wallet_id", "created_at"])

    if "ix_recommendation_snapshots_user_id_snapshot_date" not in _indexes("recommendation_snapshots"):
        op.create_index(
            "ix_recommendation_snapshots_user_id_snapshot_date",
            "recommendation_snapshots",
            ["user_id", "snapshot_date"],
        )


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index("ix_recommendation_snapshots_user_id_snapshot_date", table_name="recommendation_snapshots")
        op.drop_index("ix_transactions_wallet_id_created_at", table_name="transactions")
        op.drop_index("ix_tasks_building_code_status", table_name="tasks")
        op.drop_index("ix_tasks_status_created_at", table_name="tasks")
        op.drop_constraint("uq_transactions_settlement_key", "transactions", type_="unique")
        op.drop_column("transactions", "settlement_key")
        op.drop_constraint("uq_ratings_task_id_from_user_id", "ratings", type_="unique")
        return

    if "ix_recommendation_snapshots_user_id_snapshot_date" in _indexes("recommendation_snapshots"):
        op.drop_index("ix_recommendation_snapshots_user_id_snapshot_date", table_name="recommendation_snapshots")
    if "ix_transactions_wallet_id_created_at" in _indexes("transactions"):
        op.drop_index("ix_transactions_wallet_id_created_at", table_name="transactions")
    if "ix_tasks_building_code_status" in _indexes("tasks"):
        op.drop_index("ix_tasks_building_code_status", table_name="tasks")
    if "ix_tasks_status_created_at" in _indexes("tasks"):
        op.drop_index("ix_tasks_status_created_at", table_name="tasks")

    if "uq_transactions_settlement_key" in _unique_constraints("transactions"):
        op.drop_constraint("uq_transactions_settlement_key", "transactions", type_="unique")
    if "settlement_key" in _columns("transactions"):
        op.drop_column("transactions", "settlement_key")

    if "uq_ratings_task_id_from_user_id" in _unique_constraints("ratings"):
        op.drop_constraint("uq_ratings_task_id_from_user_id", "ratings", type_="unique")
