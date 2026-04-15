"""initial schema

Revision ID: 20260415_000001
Revises: 
Create Date: 2026-04-15 20:00:00
"""
from __future__ import annotations

from alembic import op

from app import models  # noqa: F401
from app.models.base import Base

# revision identifiers, used by Alembic.
revision = "20260415_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
