"""
文件说明：
这是地图路由文件。
负责楼宇点位查询和附近任务查询接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.map_service import list_buildings as list_buildings_service, list_nearby_tasks as list_nearby_tasks_service
from app.utils.response import success

router = APIRouter(prefix="/map", tags=["Map"])


@router.get("/buildings")
def list_buildings(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    return success(list_buildings_service(db))


@router.get("/tasks/nearby")
def list_nearby_tasks(
    buildingCode: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    return success(list_nearby_tasks_service(db, building_code=buildingCode, limit=limit))
