"""
文件说明：
这是智能推荐路由占位文件。
B 同学后续应在这里提供推荐任务列表与推荐得分解释接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.recommendation_service import build_stub_recommendation
from app.utils.response import success

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


@router.get("/tasks")
def list_recommended_tasks() -> dict:
    return success([build_stub_recommendation()])

