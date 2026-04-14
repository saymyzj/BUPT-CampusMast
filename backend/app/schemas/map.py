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
    xCoord: float
    yCoord: float


class NearbyTaskResponse(TaskResponse):
    distanceScore: float

