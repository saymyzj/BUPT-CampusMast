"""
文件说明：
这是地图路由占位文件。
组长后续应在这里接入楼宇点位查询和附近任务查询接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.map_service import build_stub_building
from app.services.task_service import build_stub_task
from app.utils.response import success

router = APIRouter(prefix="/map", tags=["Map"])


@router.get("/buildings")
def list_buildings() -> dict:
    return success([build_stub_building()])


@router.get("/tasks/nearby")
def list_nearby_tasks() -> dict:
    task = build_stub_task()
    task["distanceScore"] = 12.5
    return success([task])

