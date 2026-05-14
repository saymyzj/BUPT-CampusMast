"""
文件说明：
这是用户与用户画像模型文件。
它承载双信用分、常用楼宇、偏好类别等推荐与权限都会依赖的基础信息。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    student_email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    requester_credit_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100, nullable=False)
    helper_credit_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100, nullable=False)
    overall_credit_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), primary_key=True)
    default_building_code: Mapped[str | None] = mapped_column(String(32))
    preferred_categories: Mapped[str | None] = mapped_column(String(500))
    active_time_slots: Mapped[str | None] = mapped_column(String(500))
    helper_success_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

