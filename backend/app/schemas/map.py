"""
文件说明：
这是地图模块的 Schema 文件。
用于统一楼宇点位和附近任务查询的返回结构。
"""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.task import TaskResponse


class CampusBuildingResponse(BaseModel):
    code: str
    name: str
    campusZone: str | None = None
    latitude: float
    longitude: float
    polygon: list[list[float]] | list[list[list[float]]] | None = None


class NearbyTaskResponse(TaskResponse):
    distanceScore: float
