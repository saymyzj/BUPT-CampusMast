"""
文件说明：
这是通知服务文件。
负责通知落库、列表查询、已读更新与 WebSocket 推送。
"""
from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.serialization import to_iso8601
from app.websockets.events import NOTIFICATION_CREATED, UNREAD_SYNC
from app.websockets.manager import manager


def list_notifications(db: Session, *, user_id: str, page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    total = query.count()
    rows = query.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return [serialize_notification(row) for row in rows], total


def mark_notification_read(db: Session, *, user_id: str, notification_id: str) -> dict[str, Any]:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise AppError("NOTIFICATION_NOT_FOUND", "通知不存在", status.HTTP_404_NOT_FOUND)
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return serialize_notification(notification)


def mark_all_notifications_read(db: Session, *, user_id: str) -> int:
    rows = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).all()
    for row in rows:
        row.is_read = True
    db.commit()
    return len(rows)


def get_unread_count(db: Session, *, user_id: str) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).count()


def create_notification(
    db: Session,
    *,
    user_id: str,
    type_: str,
    title: str,
    body: str,
    related_task_id: str | None = None,
) -> Notification:
    row = Notification(
        id=generate_id("notify"),
        user_id=user_id,
        type=type_,
        title=title,
        body=body,
        related_task_id=related_task_id,
        is_read=False,
    )
    db.add(row)
    db.flush()
    return row


async def push_notification_events(db: Session, *, user_id: str, notification: Notification) -> None:
    await manager.broadcast(f"notification:{user_id}", NOTIFICATION_CREATED, serialize_notification(notification))
    await manager.broadcast(f"notification:{user_id}", UNREAD_SYNC, {"unreadCount": get_unread_count(db, user_id=user_id)})


def serialize_notification(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "body": notification.body,
        "relatedTaskId": notification.related_task_id,
        "isRead": notification.is_read,
        "createdAt": to_iso8601(notification.created_at),
    }
