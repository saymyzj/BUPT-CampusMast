"""
文件说明：
这是评价与信用快照模型文件。
它为双分制加权信用模型提供持久化基础。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("task_id", "from_user_id", name="uq_ratings_task_id_from_user_id"),)

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(25), ForeignKey("tasks.id"), nullable=False)
    from_user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    to_user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CreditSnapshot(Base):
    __tablename__ = "credit_snapshots"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    role_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    completion_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    average_rating: Mapped[float | None] = mapped_column(Numeric(5, 2))
    timeout_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    abandon_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    dispute_lose_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    malicious_dispute_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    post_accept_cancel_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    calculated_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
