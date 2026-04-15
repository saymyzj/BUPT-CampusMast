"""
文件说明：
这是地图服务文件。
负责楼宇点位读取与附近任务查询。
"""
from __future__ import annotations

from math import sqrt
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.models.map import CampusBuilding
from app.models.task import Task
from app.models.user import User
from app.utils.errors import AppError
from app.utils.serialization import decimal_to_money, json_loads


def list_buildings(db: Session) -> list[dict[str, Any]]:
    rows = db.query(CampusBuilding).filter(CampusBuilding.is_active.is_(True)).order_by(CampusBuilding.code.asc()).all()
    return [serialize_building(row) for row in rows]


def list_nearby_tasks(db: Session, *, building_code: str, limit: int) -> list[dict[str, Any]]:
    source = db.get(CampusBuilding, building_code)
    if source is None:
        raise AppError("BUILDING_NOT_FOUND", "楼宇不存在", status.HTTP_404_NOT_FOUND)

    buildings = {item.code: item for item in db.query(CampusBuilding).filter(CampusBuilding.is_active.is_(True)).all()}
    tasks = db.query(Task).filter(Task.building_code.is_not(None)).order_by(Task.created_at.desc()).all()
    result = []
    for task in tasks:
        target = buildings.get(task.building_code)
        if target is None:
            continue
        distance = sqrt((source.latitude - target.latitude) ** 2 + (source.longitude - target.longitude) ** 2) * 100000
        result.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "category": task.category.value if hasattr(task.category, "value") else task.category,
                "reward": decimal_to_money(task.reward),
                "status": task.status.value if hasattr(task.status, "value") else task.status,
                "buildingCode": task.building_code,
                "locationDetail": task.location_detail,
                "requester": _serialize_user_summary(db.get(User, task.requester_id), task.requester_id),
                "helper": (
                    _serialize_user_summary(db.get(User, task.helper_id), task.helper_id)
                    if task.helper_id
                    else None
                ),
                "moderationResult": task.moderation_result.value if hasattr(task.moderation_result, "value") else task.moderation_result,
                "needsAdminReview": task.needs_admin_review,
                "distanceScore": round(distance, 2),
            }
        )
    return sorted(result, key=lambda item: item["distanceScore"])[:limit]


def serialize_building(row: CampusBuilding) -> dict[str, Any]:
    return {
        "code": row.code,
        "name": row.name,
        "campusZone": row.campus_zone,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "polygon": json_loads(row.polygon_json, None),
    }


def _serialize_user_summary(user: User | None, user_id: str | None) -> dict[str, Any]:
    return {
        "id": user_id,
        "nickname": user.nickname if user else "用户",
        "overallCreditScore": float(user.overall_credit_score) if user else 100,
    }
