"""
文件说明：
这是通知模型文件。
站内通知列表查询依赖这里，WebSocket 实时通知则与 notification_service 配合完成。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String(25))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

