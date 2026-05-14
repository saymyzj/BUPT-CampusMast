"""
文件说明：
这是 AI 审核记录模型文件。
DeepSeek 审核结果、高危拦截和低危复审都依赖这里留痕。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModerationRecord(Base):
    __tablename__ = "moderation_records"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    task_id: Mapped[str | None] = mapped_column(String(25), ForeignKey("tasks.id"))
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="DEEPSEEK", nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    hit_tags: Mapped[str | None] = mapped_column(Text)
    model_output: Mapped[str | None] = mapped_column(Text)
    admin_review_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    admin_review_note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)

