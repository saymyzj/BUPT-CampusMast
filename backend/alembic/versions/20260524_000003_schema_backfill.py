"""backfill schema objects introduced after initial migration

Revision ID: 20260524_000003
Revises: 20260518_000002
Create Date: 2026-05-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app import models  # noqa: F401
from app.models.base import Base
from app.models.enums import ModerationResult, Role, TaskCategory, TaskStatus


revision = "20260524_000003"
down_revision = "20260518_000002"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return _inspector().has_table(table_name)


def _columns(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if _has_table(table_name) and column.name not in _columns(table_name):
        op.add_column(table_name, column)


def _create_index_if_possible(index_name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if not _has_table(table_name):
        return
    if not set(columns).issubset(_columns(table_name)):
        return
    if index_name in _indexes(table_name):
        return
    op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    # Older local databases may already be stamped at the initial revision but
    # still miss later model fields. Add columns first, then create any missing
    # tables from current metadata.
    _add_column_if_missing("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))
    _add_column_if_missing("users", sa.Column("phone", sa.String(length=20), nullable=True))
    _add_column_if_missing(
        "users",
        sa.Column("role", sa.Enum(Role), nullable=False, server_default=Role.USER.name),
    )
    _add_column_if_missing(
        "users",
        sa.Column("requester_credit_score", sa.Numeric(5, 2), nullable=False, server_default="100.00"),
    )
    _add_column_if_missing(
        "users",
        sa.Column("helper_credit_score", sa.Numeric(5, 2), nullable=False, server_default="100.00"),
    )
    _add_column_if_missing(
        "users",
        sa.Column("overall_credit_score", sa.Numeric(5, 2), nullable=False, server_default="100.00"),
    )
    _add_column_if_missing("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add_column_if_missing("users", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    _add_column_if_missing("users", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()))

    _add_column_if_missing("tasks", sa.Column("category", sa.Enum(TaskCategory), nullable=False, server_default=TaskCategory.OTHER.name))
    _add_column_if_missing("tasks", sa.Column("status", sa.Enum(TaskStatus), nullable=False, server_default=TaskStatus.PENDING.name))
    _add_column_if_missing("tasks", sa.Column("building_code", sa.String(length=32), nullable=False, server_default=""))
    _add_column_if_missing("tasks", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing("tasks", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    _add_column_if_missing("tasks", sa.Column("location_detail", sa.String(length=200), nullable=True))
    _add_column_if_missing("tasks", sa.Column("image_urls", sa.Text(), nullable=True))
    _add_column_if_missing("tasks", sa.Column("helper_id", sa.String(length=25), nullable=True))
    _add_column_if_missing("tasks", sa.Column("proof_note", sa.Text(), nullable=True))
    _add_column_if_missing("tasks", sa.Column("proof_image_urls", sa.Text(), nullable=True))
    _add_column_if_missing(
        "tasks",
        sa.Column("moderation_result", sa.Enum(ModerationResult), nullable=False, server_default=ModerationResult.ALLOW.name),
    )
    _add_column_if_missing("tasks", sa.Column("needs_admin_review", sa.Boolean(), nullable=False, server_default=sa.false()))
    _add_column_if_missing("tasks", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    _add_column_if_missing("tasks", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))
    _add_column_if_missing("tasks", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()))
    _add_column_if_missing("tasks", sa.Column("completed_at", sa.DateTime(), nullable=True))

    _add_column_if_missing("wallets", sa.Column("frozen", sa.Numeric(10, 2), nullable=False, server_default="0.00"))
    _add_column_if_missing("wallets", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()))

    _add_column_if_missing("transactions", sa.Column("related_task_id", sa.String(length=25), nullable=True))
    _add_column_if_missing("transactions", sa.Column("settlement_key", sa.String(length=25), nullable=True))
    _add_column_if_missing("transactions", sa.Column("description", sa.String(length=200), nullable=True))
    _add_column_if_missing("transactions", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()))

    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)

    _create_index_if_possible("ix_tasks_status_created_at", "tasks", ["status", "created_at"])
    _create_index_if_possible("ix_tasks_building_code_status", "tasks", ["building_code", "status"])
    _create_index_if_possible("ix_transactions_wallet_id_created_at", "transactions", ["wallet_id", "created_at"])
    _create_index_if_possible(
        "ix_recommendation_snapshots_user_id_snapshot_date",
        "recommendation_snapshots",
        ["user_id", "snapshot_date"],
    )
    _create_index_if_possible("uq_ratings_task_id_from_user_id", "ratings", ["task_id", "from_user_id"], unique=True)
    _create_index_if_possible("uq_transactions_settlement_key", "transactions", ["settlement_key"], unique=True)


def downgrade() -> None:
    # The migration is a compatibility backfill for already-running local
    # databases. Dropping columns/tables here would be unsafe and unnecessary.
    pass
