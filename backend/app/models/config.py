"""
文件说明：
这是系统配置与首页内容配置模型文件。
组长后续会在管理后台通过这两个模型维护接单门槛、信用权重、审核阈值和首页内容。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    config_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    config_group: Mapped[str] = mapped_column(String(50), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    updated_by: Mapped[str | None] = mapped_column(String(25), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class HomepageBlock(Base):
    __tablename__ = "homepage_blocks"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    block_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(25), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

