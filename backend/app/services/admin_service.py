"""
文件说明：
这是后台服务文件。
负责用户、任务、审核记录与统计摘要的后台查询和更新。
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage
from app.models.moderation import ModerationRecord
from app.models.task import Task
from app.models.user import User
from app.schemas.admin import AdminResolveDisputeRequest, AdminUpdateUserRequest
from app.services.auth_service import serialize_user
from app.services.moderation_service import serialize_moderation_record
from app.services.task_service import (
    TaskError,
    close_dispute_by_admin,
    resolve_dispute_for_helper,
    resolve_dispute_for_requester,
    resolve_dispute_split,
)
from app.services.wallet_service import WalletError
from app.utils.errors import AppError
from app.utils.serialization import decimal_to_money, to_iso8601


def list_users(db: Session, *, page: int, limit: int, keyword: str | None = None) -> tuple[list[dict[str, Any]], int]:
    query = db.query(User)
    if keyword:
        like = f"%{keyword.strip()}%"
        query = query.filter((User.student_email.like(like)) | (User.nickname.like(like)))
    total = query.count()
    rows = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return [serialize_user(db, row).model_dump() for row in rows], total


def update_user(db: Session, *, user_id: str, payload: AdminUpdateUserRequest) -> dict[str, Any]:
    user = db.get(User, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", status.HTTP_404_NOT_FOUND)

    if payload.isActive is not None:
        user.is_active = payload.isActive
    if payload.requesterCreditScore is not None:
        user.requester_credit_score = payload.requesterCreditScore
    if payload.helperCreditScore is not None:
        user.helper_credit_score = payload.helperCreditScore
    if payload.requesterCreditScore is not None or payload.helperCreditScore is not None:
        user.overall_credit_score = round(float(user.requester_credit_score) * 0.4 + float(user.helper_credit_score) * 0.6, 2)

    db.commit()
    db.refresh(user)
    return serialize_user(db, user).model_dump()


def list_tasks(
    db: Session,
    *,
    page: int,
    limit: int,
    status_filter: str | None = None,
    needs_admin_review: bool | None = None,
) -> tuple[list[dict[str, Any]], int]:
    query = db.query(Task)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if needs_admin_review is not None:
        query = query.filter(Task.needs_admin_review == needs_admin_review)
    total = query.count()
    rows = query.order_by(Task.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return [serialize_task_for_admin(db, row) for row in rows], total


def _raise_dispute_app_error(exc: TaskError | WalletError) -> None:
    if exc.code == "TASK_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code in {"INVALID_SPLIT_RATIO", "INVALID_DISPUTE_RESOLUTION"}:
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_409_CONFLICT
    raise AppError(exc.code, exc.message, status_code) from exc


def resolve_dispute(db: Session, *, task_id: str, payload: AdminResolveDisputeRequest, admin_id: str) -> dict[str, Any]:
    resolution = payload.resolution.lower()
    try:
        if resolution == "refund":
            task = resolve_dispute_for_requester(db, task_id, admin_id, payload.note)
        elif resolution == "settle":
            task = resolve_dispute_for_helper(db, task_id, admin_id, payload.note)
        elif resolution == "split":
            if payload.splitRatio is None:
                raise AppError("SPLIT_RATIO_REQUIRED", "splitRatio is required when resolution is split", status.HTTP_400_BAD_REQUEST)
            task = resolve_dispute_split(db, task_id, admin_id, Decimal(str(payload.splitRatio)), payload.note)
        elif resolution == "close":
            task = close_dispute_by_admin(db, task_id, admin_id, payload.note)
        else:
            raise AppError("INVALID_RESOLUTION", "无效的争议处理结果", status.HTTP_400_BAD_REQUEST)
    except (TaskError, WalletError) as exc:
        _raise_dispute_app_error(exc)

    return serialize_task_for_admin(db, task)


def build_admin_stats(db: Session) -> dict[str, int]:
    return {
        "userCount": db.query(User).count(),
        "taskCount": db.query(Task).count(),
        "messageCount": db.query(ChatMessage).count(),
        "moderationReviewPending": db.query(ModerationRecord).filter(ModerationRecord.admin_review_status == "PENDING").count(),
    }


def serialize_task_for_admin(db: Session, task: Task) -> dict[str, Any]:
    requester = db.get(User, task.requester_id)
    helper = db.get(User, task.helper_id) if task.helper_id else None
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "category": task.category.value if hasattr(task.category, "value") else task.category,
        "reward": decimal_to_money(task.reward),
        "status": task.status.value if hasattr(task.status, "value") else task.status,
        "buildingCode": task.building_code,
        "latitude": float(task.latitude) if task.latitude is not None else None,
        "longitude": float(task.longitude) if task.longitude is not None else None,
        "locationDetail": task.location_detail,
        "requester": {
            "id": task.requester_id,
            "nickname": requester.nickname if requester else "请求方",
            "overallCreditScore": float(requester.overall_credit_score) if requester else 100,
        },
        "helper": (
            {
                "id": task.helper_id,
                "nickname": helper.nickname if helper else "接单方",
                "overallCreditScore": float(helper.overall_credit_score) if helper else 100,
            }
            if task.helper_id
            else None
        ),
        "moderationResult": task.moderation_result.value if hasattr(task.moderation_result, "value") else task.moderation_result,
        "needsAdminReview": task.needs_admin_review,
        "deadline": to_iso8601(task.deadline),
        "imageUrls": [],
        "createdAt": to_iso8601(task.created_at),
    }
