"""
文件说明：
这是智能推荐快照模型文件。
它用于记录规则加权推荐结果，方便调参与后台统计。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RecommendationSnapshot(Base):
    __tablename__ = "recommendation_snapshots"
    __table_args__ = (Index("ix_recommendation_snapshots_user_id_snapshot_date", "user_id", "snapshot_date"),)

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(25), ForeignKey("tasks.id"), nullable=False)
    score_total: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    score_category: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    score_distance: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    score_success_rate: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    score_active_time: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
