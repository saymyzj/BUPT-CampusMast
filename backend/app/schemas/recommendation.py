"""
文件说明：
这是智能推荐模块的 Schema 文件。
它把任务推荐结果拆成总分与分项得分，便于调参与后台展示。
"""
from __future__ import annotations

from pydantic import BaseModel

from app.schemas.task import TaskResponse


class RecommendationItemResponse(BaseModel):
    task: TaskResponse
    scoreTotal: float
    scoreCategory: float
    scoreDistance: float
    scoreSuccessRate: float
    scoreActiveTime: float
    recommendation: dict
