"""
文件说明：
这是数据库会话依赖文件。
FastAPI 路由层通过这里向 Service 层注入 SQLAlchemy Session，避免每个路由自行创建连接。
"""
from __future__ import annotations

from collections.abc import Generator

from app.models.base import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
      yield db
    finally:
      db.close()

