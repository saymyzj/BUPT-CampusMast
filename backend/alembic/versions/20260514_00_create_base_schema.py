"""create base schema

Revision ID: 20260514_00
Revises:
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260514_00"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("student_email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role", sa.Enum("USER", "ADMIN", name="role"), nullable=False),
        sa.Column("requester_credit_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("helper_credit_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("overall_credit_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_student_email", "users", ["student_email"], unique=True)

    op.create_table(
        "campus_buildings",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("campus_zone", sa.String(length=50), nullable=True),
        sa.Column("x_coord", sa.Float(), nullable=False),
        sa.Column("y_coord", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("default_building_code", sa.String(length=32), nullable=True),
        sa.Column("preferred_categories", sa.String(length=500), nullable=True),
        sa.Column("active_time_slots", sa.String(length=500), nullable=True),
        sa.Column("helper_success_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "wallets",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("available", sa.Numeric(10, 2), nullable=False),
        sa.Column("frozen", sa.Numeric(10, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "system_configs",
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_group", sa.String(length=50), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("updated_by", sa.String(length=25), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("config_key"),
    )

    op.create_table(
        "homepage_blocks",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("block_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("updated_by", sa.String(length=25), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Enum("PACKAGE", "FOOD", "MOVE", "OTHER", name="taskcategory"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "PENDING_REVIEW",
                "COMPLETED",
                "DISPUTED",
                "CANCELLED",
                "EXPIRED",
                "CLOSED_BY_ADMIN",
                name="taskstatus",
            ),
            nullable=False,
        ),
        sa.Column("reward", sa.Numeric(10, 2), nullable=False),
        sa.Column("building_code", sa.String(length=32), nullable=False),
        sa.Column("location_detail", sa.String(length=200), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=False),
        sa.Column("image_urls", sa.Text(), nullable=True),
        sa.Column("requester_id", sa.String(length=25), nullable=False),
        sa.Column("helper_id", sa.String(length=25), nullable=True),
        sa.Column("proof_note", sa.Text(), nullable=True),
        sa.Column("proof_image_urls", sa.Text(), nullable=True),
        sa.Column("moderation_result", sa.Enum("ALLOW", "REVIEW", "BLOCK", name="moderationresult"), nullable=False),
        sa.Column("needs_admin_review", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["helper_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("wallet_id", sa.String(length=25), nullable=False),
        sa.Column(
            "type",
            sa.Enum("TOP_UP", "WITHDRAW", "FREEZE", "UNFREEZE", "SETTLE_OUT", "SETTLE_IN", "SETTLE_SPLIT", name="transactiontype"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("related_task_id", sa.String(length=25), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "task_logs",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("task_id", sa.String(length=25), nullable=False),
        sa.Column(
            "from_status",
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "PENDING_REVIEW",
                "COMPLETED",
                "DISPUTED",
                "CANCELLED",
                "EXPIRED",
                "CLOSED_BY_ADMIN",
                name="taskstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "to_status",
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "PENDING_REVIEW",
                "COMPLETED",
                "DISPUTED",
                "CANCELLED",
                "EXPIRED",
                "CLOSED_BY_ADMIN",
                name="taskstatus",
            ),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(length=25), nullable=False),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ratings",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("task_id", sa.String(length=25), nullable=False),
        sa.Column("from_user_id", sa.String(length=25), nullable=False),
        sa.Column("to_user_id", sa.String(length=25), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "credit_snapshots",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("role_scope", sa.String(length=20), nullable=False),
        sa.Column("completion_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("average_rating", sa.Numeric(5, 2), nullable=True),
        sa.Column("timeout_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("abandon_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("dispute_lose_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("malicious_dispute_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("post_accept_cancel_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("calculated_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recommendation_snapshots",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("task_id", sa.String(length=25), nullable=False),
        sa.Column("score_total", sa.Numeric(6, 2), nullable=False),
        sa.Column("score_category", sa.Numeric(6, 2), nullable=False),
        sa.Column("score_distance", sa.Numeric(6, 2), nullable=False),
        sa.Column("score_success_rate", sa.Numeric(6, 2), nullable=False),
        sa.Column("score_active_time", sa.Numeric(6, 2), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("related_task_id", sa.String(length=25), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("task_id", sa.String(length=25), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )

    op.create_table(
        "chat_participants",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("conversation_id", sa.String(length=25), nullable=False),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("unread_count", sa.Integer(), nullable=False),
        sa.Column("last_read_message_id", sa.String(length=25), nullable=True),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("conversation_id", sa.String(length=25), nullable=False),
        sa.Column("sender_id", sa.String(length=25), nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("client_message_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversations.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "moderation_records",
        sa.Column("id", sa.String(length=25), nullable=False),
        sa.Column("task_id", sa.String(length=25), nullable=True),
        sa.Column("user_id", sa.String(length=25), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("hit_tags", sa.Text(), nullable=True),
        sa.Column("model_output", sa.Text(), nullable=True),
        sa.Column("admin_review_status", sa.String(length=20), nullable=False),
        sa.Column("admin_review_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("moderation_records")
    op.drop_table("chat_messages")
    op.drop_table("chat_participants")
    op.drop_table("chat_conversations")
    op.drop_table("notifications")
    op.drop_table("recommendation_snapshots")
    op.drop_table("credit_snapshots")
    op.drop_table("ratings")
    op.drop_table("task_logs")
    op.drop_table("transactions")
    op.drop_table("tasks")
    op.drop_table("homepage_blocks")
    op.drop_table("system_configs")
    op.drop_table("wallets")
    op.drop_table("user_profiles")
    op.drop_table("campus_buildings")
    op.drop_index("ix_users_student_email", table_name="users")
    op.drop_table("users")
