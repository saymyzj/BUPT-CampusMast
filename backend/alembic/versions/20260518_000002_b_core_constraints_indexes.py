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
    if not inspector.has_table(table_name):
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_constraints(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table_name)


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _create_unique(table_name: str, name: str, columns: list[str]) -> None:
    if _is_sqlite():
        if name not in _indexes(table_name):
            op.create_index(name, table_name, columns, unique=True)
        return
    op.create_unique_constraint(name, table_name, columns)


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

    rating_columns = _columns("ratings")
    if (
        _has_table("ratings")
        and {"task_id", "from_user_id"}.issubset(rating_columns)
        and "uq_ratings_task_id_from_user_id" not in _unique_constraints("ratings")
        and "uq_ratings_task_id_from_user_id" not in _indexes("ratings")
    ):
        _create_unique(
            "ratings",
            "uq_ratings_task_id_from_user_id",
            ["task_id", "from_user_id"],
        )

    transaction_columns = _columns("transactions")
    if _has_table("transactions") and "settlement_key" not in transaction_columns:
        op.add_column("transactions", sa.Column("settlement_key", sa.String(length=25), nullable=True))
    transaction_columns = _columns("transactions")
    if (
        _has_table("transactions")
        and "settlement_key" in transaction_columns
        and "uq_transactions_settlement_key" not in _unique_constraints("transactions")
        and "uq_transactions_settlement_key" not in _indexes("transactions")
    ):
        _create_unique(
            "transactions",
            "uq_transactions_settlement_key",
            ["settlement_key"],
        )

    if _has_table("tasks"):
        task_columns = _columns("tasks")
        task_indexes = _indexes("tasks")
        if {"status", "created_at"}.issubset(task_columns) and "ix_tasks_status_created_at" not in task_indexes:
            op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
        if {"building_code", "status"}.issubset(task_columns) and "ix_tasks_building_code_status" not in task_indexes:
            op.create_index("ix_tasks_building_code_status", "tasks", ["building_code", "status"])

    transaction_columns = _columns("transactions")
    if (
        _has_table("transactions")
        and {"wallet_id", "created_at"}.issubset(transaction_columns)
        and "ix_transactions_wallet_id_created_at" not in _indexes("transactions")
    ):
        op.create_index("ix_transactions_wallet_id_created_at", "transactions", ["wallet_id", "created_at"])

    recommendation_columns = _columns("recommendation_snapshots")
    if (
        _has_table("recommendation_snapshots")
        and {"user_id", "snapshot_date"}.issubset(recommendation_columns)
        and "ix_recommendation_snapshots_user_id_snapshot_date" not in _indexes("recommendation_snapshots")
    ):
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
