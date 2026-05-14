"""add wallet settlement idempotency guard

Revision ID: 20260514_02
Revises: 20260514_01
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260514_02"
down_revision = "20260514_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("settlement_key", sa.String(length=25), nullable=True))
    op.create_unique_constraint(
        "uq_transactions_settlement_key",
        "transactions",
        ["settlement_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_transactions_settlement_key",
        "transactions",
        type_="unique",
    )
    op.drop_column("transactions", "settlement_key")
