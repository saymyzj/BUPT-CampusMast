"""
文件说明：
这是通知路由文件。
负责通知分页查询、单条已读与全部已读接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.notification_service import (
    get_unread_count,
    list_notifications as list_notifications_service,
    mark_all_notifications_read as mark_all_notifications_read_service,
    mark_notification_read as mark_notification_read_service,
)
from app.utils.response import success

router = APIRouter(prefix="/notifications", tags=["Notification"])


@router.get("")
def list_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = list_notifications_service(db, user_id=user.id, page=page, limit=limit)
    return success(rows, meta={"page": page, "limit": limit, "total": total, "unreadCount": get_unread_count(db, user_id=user.id)})


@router.patch("/{id}/read")
def mark_notification_read(id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return success(mark_notification_read_service(db, user_id=user.id, notification_id=id))


@router.patch("/read-all")
def mark_all_notifications_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    updated_count = mark_all_notifications_read_service(db, user_id=user.id)
    return success({"updatedCount": updated_count, "unreadCount": 0})
