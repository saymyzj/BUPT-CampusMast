"""add rating duplicate guard

Revision ID: 20260514_01
Revises: 20260514_00
Create Date: 2026-05-14
"""

from __future__ import annotations

from alembic import op


revision = "20260514_01"
down_revision = "20260514_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_ratings_task_id_from_user_id",
        "ratings",
        ["task_id", "from_user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ratings_task_id_from_user_id",
        "ratings",
        type_="unique",
    )
