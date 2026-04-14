"""
文件说明：
这是校园地图楼宇点位模型文件。
北邮校园平面图的自定义楼宇坐标和后台运营配置都将依赖这里。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CampusBuilding(Base):
    __tablename__ = "campus_buildings"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    campus_zone: Mapped[str | None] = mapped_column(String(50))
    x_coord: Mapped[float] = mapped_column(nullable=False)
    y_coord: Mapped[float] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

