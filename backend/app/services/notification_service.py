"""
Durable notification helpers.

WebSocket gateway ownership is outside member B. These helpers write the
notification rows and publish a best-effort Redis event that the gateway can
consume when that module is wired by the owner.
"""
from __future__ import annotations

import json

from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.models.enums import Role
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.services.wallet_service import new_id
from app.utils.redis import get_redis_client

TASK_EVENT_COPY = {
    "TASK_ACCEPTED": ("Task accepted", "Your task has been accepted."),
    "TASK_SUBMITTED": ("Task submitted", "The helper has submitted completion proof."),
    "TASK_CONFIRMED": ("Task confirmed", "The task has been confirmed."),
    "TASK_REJECTED": ("Task rejected", "The submitted proof was rejected."),
    "TASK_CANCELLED": ("Task cancelled", "The task has been cancelled or expired."),
    "TASK_DISPUTED": ("Task disputed", "The task has entered dispute handling."),
    "DISPUTE_RESOLVED": ("Dispute resolved", "The dispute has been resolved."),
}


def notification_to_dict(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "body": notification.body,
        "relatedTaskId": notification.related_task_id,
        "isRead": notification.is_read,
        "createdAt": notification.created_at.isoformat() if notification.created_at else "",
    }


def _publish_notification(notification: Notification) -> None:
    try:
        get_redis_client().publish(
            f"notifications:user:{notification.user_id}",
            json.dumps(notification_to_dict(notification), ensure_ascii=False),
        )
    except RedisError:
        return None


def create_notification(
    db: Session,
    user_id: str,
    event_type: str,
    title: str,
    body: str,
    *,
    related_task_id: str | None = None,
) -> Notification:
    notification = Notification(
        id=new_id("notify"),
        user_id=user_id,
        type=event_type,
        title=title,
        body=body,
        related_task_id=related_task_id,
        is_read=False,
    )
    db.add(notification)
    db.flush()
    _publish_notification(notification)
    return notification


def _task_event_recipients(db: Session, task: Task, event_name: str) -> list[str]:
    recipients: set[str] = set()
    if event_name in {"TASK_ACCEPTED", "TASK_SUBMITTED"}:
        recipients.add(task.requester_id)
    elif event_name in {"TASK_CONFIRMED", "TASK_REJECTED"} and task.helper_id:
        recipients.add(task.helper_id)
    elif event_name in {"TASK_CANCELLED", "DISPUTE_RESOLVED"}:
        recipients.add(task.requester_id)
        if task.helper_id:
            recipients.add(task.helper_id)
    elif event_name == "TASK_DISPUTED":
        recipients.add(task.requester_id)
        if task.helper_id:
            recipients.add(task.helper_id)
        admin_ids = db.query(User.id).filter(User.role == Role.ADMIN).all()
        recipients.update(row[0] for row in admin_ids)
    return sorted(recipients)


def notify_task_event(db: Session, task: Task, event_name: str) -> list[Notification]:
    title, body = TASK_EVENT_COPY.get(event_name, ("Task update", "The task status has changed."))
    return [
        create_notification(
            db,
            user_id,
            event_name,
            title,
            body,
            related_task_id=task.id,
        )
        for user_id in _task_event_recipients(db, task, event_name)
    ]


def build_stub_notification() -> dict:
    return {
        "id": "notify_stub",
        "type": "SYSTEM_NOTICE",
        "title": "Scaffold notification",
        "body": "This is a scaffold notification for integration checks.",
        "relatedTaskId": None,
        "isRead": False,
        "createdAt": "2026-04-14T00:00:00Z",
    }
