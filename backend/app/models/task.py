"""
文件说明：
这是任务和任务日志模型文件。
这里定义了冻结版状态机所需要的核心字段，包括楼宇定位、审核结果和乐观锁版本号。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ModerationResult, TaskCategory, TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TaskCategory] = mapped_column(Enum(TaskCategory), nullable=False)
    reward: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    building_code: Mapped[str] = mapped_column(String(32), nullable=False)
    location_detail: Mapped[str | None] = mapped_column(String(200))
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    image_urls: Mapped[str | None] = mapped_column(Text)
    requester_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    helper_id: Mapped[str | None] = mapped_column(String(25), ForeignKey("users.id"))
    proof_note: Mapped[str | None] = mapped_column(Text)
    proof_image_urls: Mapped[str | None] = mapped_column(Text)
    moderation_result: Mapped[ModerationResult] = mapped_column(
        Enum(ModerationResult), default=ModerationResult.ALLOW, nullable=False
    )
    needs_admin_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(25), ForeignKey("tasks.id"), nullable=False)
    from_status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False)
    to_status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

