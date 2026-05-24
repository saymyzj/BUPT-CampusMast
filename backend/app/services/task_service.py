from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatConversation, ChatParticipant
from app.models.config import SystemConfig
from app.models.enums import ModerationResult, TaskCategory, TaskStatus
from app.models.map import CampusBuilding
from app.models.task import Task, TaskLog
from app.models.user import User
from app.services.wallet_service import (
    WalletError,
    freeze_funds,
    money,
    money_text,
    new_id,
    settle_reward,
    settle_split,
    unfreeze_funds,
)

HELPER_CREDIT_THRESHOLD = Decimal("60.00")
HELPER_CREDIT_THRESHOLD_CONFIG_KEY = "helperCreditThreshold"
LEGACY_HELPER_CREDIT_THRESHOLD_CONFIG_KEY = "task.acceptance.helperCreditThreshold"

TRANSITION_RULES: dict[tuple[TaskStatus, TaskStatus], dict[str, str]] = {
    (TaskStatus.PENDING, TaskStatus.IN_PROGRESS): {
        "remark": "Task accepted by helper",
        "event": "TASK_ACCEPTED",
    },
    (TaskStatus.PENDING, TaskStatus.CANCELLED): {
        "remark": "Task cancelled by requester",
        "event": "TASK_CANCELLED",
    },
    (TaskStatus.PENDING, TaskStatus.EXPIRED): {
        "remark": "Task expired by system",
        "event": "TASK_CANCELLED",
    },
    (TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW): {
        "remark": "Completion proof submitted by helper",
        "event": "TASK_SUBMITTED",
    },
    (TaskStatus.IN_PROGRESS, TaskStatus.PENDING): {
        "remark": "Task abandoned by helper",
        "event": "TASK_CANCELLED",
    },
    (TaskStatus.IN_PROGRESS, TaskStatus.DISPUTED): {
        "remark": "Task disputed by requester",
        "event": "TASK_DISPUTED",
    },
    (TaskStatus.PENDING_REVIEW, TaskStatus.COMPLETED): {
        "remark": "Task confirmed by requester",
        "event": "TASK_CONFIRMED",
    },
    (TaskStatus.PENDING_REVIEW, TaskStatus.DISPUTED): {
        "remark": "Task review rejected by requester",
        "event": "TASK_REJECTED",
    },
    (TaskStatus.DISPUTED, TaskStatus.COMPLETED): {
        "remark": "Dispute resolved in favor of helper",
        "event": "DISPUTE_RESOLVED",
    },
    (TaskStatus.DISPUTED, TaskStatus.CANCELLED): {
        "remark": "Dispute resolved in favor of requester",
        "event": "DISPUTE_RESOLVED",
    },
    (TaskStatus.DISPUTED, TaskStatus.CLOSED_BY_ADMIN): {
        "remark": "Dispute closed by admin",
        "event": "DISPUTE_RESOLVED",
    },
}
ALLOWED_TRANSITIONS = set(TRANSITION_RULES)


class TaskError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_deadline(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as exc:
        raise TaskError("INVALID_DEADLINE", "Task deadline must be a valid ISO 8601 datetime") from exc


def _category(value: str) -> TaskCategory:
    try:
        return TaskCategory(value)
    except ValueError as exc:
        raise TaskError("INVALID_TASK_CATEGORY", "Invalid task category") from exc


def _reward(value: str | Decimal) -> Decimal:
    try:
        return money(value)
    except WalletError as exc:
        raise TaskError(exc.code, exc.message) from exc


def _user_summary(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "id": user.id,
        "nickname": user.nickname,
        "overallCreditScore": float(user.overall_credit_score),
    }


def _load_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise TaskError("USER_NOT_FOUND", "User not found")
    return user


def _load_task(db: Session, task_id: str, *, for_update: bool = False) -> Task:
    stmt = select(Task).where(Task.id == task_id)
    if for_update:
        stmt = stmt.with_for_update()
    task = db.execute(stmt).scalar_one_or_none()
    if task is None:
        raise TaskError("TASK_NOT_FOUND", "Task not found")
    return task


def _helper_credit_threshold(db: Session) -> Decimal:
    config = db.get(SystemConfig, HELPER_CREDIT_THRESHOLD_CONFIG_KEY)
    if config is None:
        config = db.get(SystemConfig, LEGACY_HELPER_CREDIT_THRESHOLD_CONFIG_KEY)
    if config is None:
        return HELPER_CREDIT_THRESHOLD
    try:
        value = json.loads(config.config_value)
        if isinstance(value, dict):
            value = value.get("value")
        threshold = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError, json.JSONDecodeError):
        return HELPER_CREDIT_THRESHOLD
    if threshold < 0 or threshold > 100:
        return HELPER_CREDIT_THRESHOLD
    return threshold.quantize(Decimal("0.01"))


def _assert_transition(from_status: TaskStatus, to_status: TaskStatus) -> None:
    if (from_status, to_status) not in ALLOWED_TRANSITIONS:
        raise TaskError(
            "INVALID_TASK_STATUS_TRANSITION",
            f"Invalid task status transition: {from_status.value} -> {to_status.value}",
        )


def _task_event_name(from_status: TaskStatus, to_status: TaskStatus) -> str:
    return TRANSITION_RULES[(from_status, to_status)]["event"]


def _emit_task_event(_db: Session, _task: Task, _event_name: str) -> None:
    from app.services.notification_service import create_notification

    recipients = {_task.requester_id}
    if _task.helper_id is not None:
        recipients.add(_task.helper_id)
    for user_id in recipients:
        create_notification(
            _db,
            user_id=user_id,
            type_=_event_name,
            title="Task status updated",
            body=f"Task {_task.id} status changed to {_task.status.value}",
            related_task_id=_task.id,
        )


def _recalculate_participant_credit(db: Session, task: Task) -> None:
    from app.services.credit_service import recalculate_user_credit

    db.flush()
    recalculate_user_credit(db, task.requester_id, commit=False)
    if task.helper_id is not None:
        recalculate_user_credit(db, task.helper_id, commit=False)


def _log_transition(
    db: Session,
    task: Task,
    from_status: TaskStatus,
    to_status: TaskStatus,
    actor_id: str,
    remark: str | None = None,
) -> None:
    db.add(
        TaskLog(
            id=new_id("log"),
            task_id=task.id,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            remark=remark,
        )
    )


def _set_status(db: Session, task: Task, to_status: TaskStatus, actor_id: str, remark: str | None = None) -> None:
    from_status = task.status
    _assert_transition(from_status, to_status)
    task.status = to_status
    task.version += 1
    log_remark = remark or TRANSITION_RULES[(from_status, to_status)]["remark"]
    _log_transition(db, task, from_status, to_status, actor_id, log_remark)
    _emit_task_event(db, task, _task_event_name(from_status, to_status))


def _ensure_chat_session(db: Session, task: Task) -> None:
    exists = db.execute(select(ChatConversation).where(ChatConversation.task_id == task.id)).scalar_one_or_none()
    if exists is not None:
        return
    conversation = ChatConversation(id=new_id("chat"), task_id=task.id, status="ACTIVE")
    db.add(conversation)
    db.flush()
    for user_id in (task.requester_id, task.helper_id):
        if user_id:
            db.add(ChatParticipant(id=new_id("part"), conversation_id=conversation.id, user_id=user_id))


def task_to_dict(db: Session, task: Task, *, include_logs: bool = False) -> dict:
    requester = db.get(User, task.requester_id)
    helper = db.get(User, task.helper_id) if task.helper_id else None
    payload = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "category": task.category.value,
        "reward": money_text(task.reward),
        "status": task.status.value,
        "buildingCode": task.building_code,
        "locationDetail": task.location_detail,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "imageUrls": json.loads(task.image_urls or "[]"),
        "requester": _user_summary(requester),
        "helper": _user_summary(helper),
        "moderationResult": task.moderation_result.value,
        "needsAdminReview": task.needs_admin_review,
        "createdAt": task.created_at.isoformat() if task.created_at else "",
    }
    if include_logs:
        logs = (
            db.query(TaskLog)
            .filter(TaskLog.task_id == task.id)
            .order_by(TaskLog.created_at.asc(), TaskLog.id.asc())
            .all()
        )
        payload.update(
            {
                "proofNote": task.proof_note,
                "proofImageUrls": json.loads(task.proof_image_urls or "[]"),
                "logs": [
                    {
                        "id": log.id,
                        "fromStatus": log.from_status.value,
                        "toStatus": log.to_status.value,
                        "actorId": log.actor_id,
                        "remark": log.remark,
                        "createdAt": log.created_at.isoformat() if log.created_at else "",
                    }
                    for log in logs
                ],
            }
        )
    return payload


def create_task(db: Session, requester_id: str, payload) -> Task:
    reward = _reward(payload.reward)
    if reward < Decimal("1.00"):
        raise TaskError("INVALID_TASK_REWARD", "Task reward must be at least 1.00")
    deadline = _parse_deadline(payload.deadline)
    if deadline <= _now():
        raise TaskError("INVALID_TASK_DEADLINE", "Task deadline must be in the future")
    _load_user(db, requester_id)
    from app.services.moderation_service import create_moderation_record, moderate_task_content

    moderation_result, hit_tags, model_output = moderate_task_content(
        user_id=requester_id,
        title=payload.title,
        description=payload.description,
        image_urls=payload.imageUrls or [],
    )
    if moderation_result == ModerationResult.BLOCK:
        create_moderation_record(
            db,
            user_id=requester_id,
            task_id=None,
            risk_level=moderation_result,
            hit_tags=hit_tags,
            model_output=model_output,
        )
        db.commit()
        raise TaskError("MODERATION_BLOCKED", "Task content was blocked by moderation")

    try:
        task = Task(
            id=new_id("task"),
            title=payload.title,
            description=payload.description,
            category=_category(payload.category),
            reward=reward,
            status=TaskStatus.PENDING,
            building_code=payload.buildingCode,
            location_detail=payload.locationDetail,
            deadline=deadline,
            image_urls=json.dumps(payload.imageUrls or []),
            requester_id=requester_id,
            moderation_result=moderation_result,
            needs_admin_review=moderation_result == ModerationResult.REVIEW,
        )
        db.add(task)
        db.flush()
        create_moderation_record(
            db,
            user_id=requester_id,
            task_id=task.id,
            risk_level=moderation_result,
            hit_tags=hit_tags,
            model_output=model_output,
        )
        freeze_funds(db, requester_id, reward, related_task_id=task.id)
        _log_transition(db, task, TaskStatus.PENDING, TaskStatus.PENDING, requester_id, "Task created and reward frozen")
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def _building_distance(db: Session, from_code: str | None, to_code: str | None) -> float | None:
    if not from_code or not to_code:
        return None
    if from_code == to_code:
        return 0.0
    origin = db.get(CampusBuilding, from_code)
    target = db.get(CampusBuilding, to_code)
    if origin is None or target is None:
        return None
    return math.dist(
        (float(origin.latitude), float(origin.longitude)),
        (float(target.latitude), float(target.longitude)),
    )


def _apply_task_sort(query, sort_by: str | None):
    if sort_by == "rewardDesc":
        return query.order_by(Task.reward.desc(), Task.created_at.desc(), Task.id.desc())
    if sort_by == "rewardAsc":
        return query.order_by(Task.reward.asc(), Task.created_at.desc(), Task.id.desc())
    if sort_by == "deadlineAsc":
        return query.order_by(Task.deadline.asc(), Task.created_at.desc(), Task.id.desc())
    return query.order_by(Task.created_at.desc(), Task.id.desc())


def list_pending_tasks(
    db: Session,
    *,
    page: int = 1,
    limit: int = 20,
    category: str | None = None,
    keyword: str | None = None,
    building_code: str | None = None,
    near_building_code: str | None = None,
    sort_by: str | None = None,
) -> tuple[list[dict], int]:
    query = db.query(Task).filter(Task.status == TaskStatus.PENDING)
    if category:
        query = query.filter(Task.category == _category(category))
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(Task.title.like(keyword_pattern) | Task.description.like(keyword_pattern))
    if building_code:
        query = query.filter(Task.building_code == building_code)
    total = query.count()
    if sort_by == "distanceAsc" and near_building_code:
        tasks = query.all()
        tasks.sort(
            key=lambda task: (
                _building_distance(db, near_building_code, task.building_code) is None,
                _building_distance(db, near_building_code, task.building_code) or 0.0,
                task.created_at or datetime.min,
                task.id,
            )
        )
        tasks = tasks[(page - 1) * limit : page * limit]
    else:
        tasks = _apply_task_sort(query, sort_by).offset((page - 1) * limit).limit(limit).all()
    return [task_to_dict(db, task) for task in tasks], total


def list_user_tasks(
    db: Session,
    user_id: str,
    *,
    role: str,
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = None,
) -> tuple[list[dict], int]:
    if role == "posted":
        query = db.query(Task).filter(Task.requester_id == user_id)
    elif role == "accepted":
        query = db.query(Task).filter(Task.helper_id == user_id)
    else:
        raise TaskError("INVALID_TASK_LIST_ROLE", "Invalid task list role")
    if status_filter:
        try:
            status = TaskStatus(status_filter)
        except ValueError as exc:
            raise TaskError("INVALID_TASK_STATUS", "Invalid task status") from exc
        query = query.filter(Task.status == status)
    total = query.count()
    tasks = query.order_by(Task.created_at.desc(), Task.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return [task_to_dict(db, task) for task in tasks], total


def get_task_by_id(db: Session, task_id: str) -> Task:
    return _load_task(db, task_id)


def expire_task(db: Session, task_id: str, actor_id: str, *, commit: bool = True) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.PENDING:
            raise TaskError("ONLY_PENDING_TASK_CAN_EXPIRE", "Only pending tasks can expire")
        _set_status(db, task, TaskStatus.EXPIRED, actor_id)
        unfreeze_funds(db, task.requester_id, task.reward, related_task_id=task.id, description="Task expired refund")
        if commit:
            db.commit()
            db.refresh(task)
        return task
    except Exception:
        if commit:
            db.rollback()
        raise


def expire_pending_tasks(db: Session, system_actor_id: str, *, now: datetime | None = None) -> list[Task]:
    cutoff = (now or _now()).replace(tzinfo=None)
    expired = (
        db.execute(
            select(Task)
            .where(Task.status == TaskStatus.PENDING, Task.deadline <= cutoff)
            .order_by(Task.deadline.asc(), Task.id.asc())
            .with_for_update()
        )
        .scalars()
        .all()
    )
    try:
        for task in expired:
            _set_status(db, task, TaskStatus.EXPIRED, system_actor_id)
            unfreeze_funds(
                db,
                task.requester_id,
                task.reward,
                related_task_id=task.id,
                description="Task expired by system refund",
            )
        db.commit()
        for task in expired:
            db.refresh(task)
        return expired
    except Exception:
        db.rollback()
        raise


def accept_task(db: Session, task_id: str, helper_id: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        helper = _load_user(db, helper_id)
        if task.requester_id == helper_id:
            raise TaskError("CANNOT_ACCEPT_OWN_TASK", "Requester cannot accept own task")
        if task.status != TaskStatus.PENDING or task.helper_id is not None:
            raise TaskError("TASK_NOT_AVAILABLE_FOR_ACCEPTANCE", "Task is not available for acceptance")
        if money(helper.helper_credit_score) < _helper_credit_threshold(db):
            raise TaskError("HELPER_CREDIT_TOO_LOW", "Helper credit score is below acceptance threshold")
        if task.deadline <= _now():
            expire_task(db, task.id, helper_id, commit=True)
            raise TaskError("TASK_EXPIRED", "Task has expired")

        from_status = task.status
        from_version = task.version
        _assert_transition(from_status, TaskStatus.IN_PROGRESS)
        updated = (
            db.query(Task)
            .filter(
                Task.id == task_id,
                Task.status == TaskStatus.PENDING,
                Task.helper_id.is_(None),
                Task.version == from_version,
            )
            .update(
                {
                    Task.helper_id: helper_id,
                    Task.status: TaskStatus.IN_PROGRESS,
                    Task.version: from_version + 1,
                },
                synchronize_session=False,
            )
        )
        if updated != 1:
            raise TaskError("TASK_ALREADY_ACCEPTED", "Task was already accepted")
        db.flush()
        db.refresh(task)
        _log_transition(
            db,
            task,
            from_status,
            TaskStatus.IN_PROGRESS,
            helper_id,
            TRANSITION_RULES[(from_status, TaskStatus.IN_PROGRESS)]["remark"],
        )
        _emit_task_event(db, task, _task_event_name(from_status, TaskStatus.IN_PROGRESS))
        _ensure_chat_session(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def submit_task_proof(db: Session, task_id: str, helper_id: str, payload) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.IN_PROGRESS:
            raise TaskError("TASK_NOT_IN_PROGRESS", "Task is not in progress")
        if task.helper_id != helper_id:
            raise TaskError("ONLY_ASSIGNED_HELPER_CAN_SUBMIT", "Only assigned helper can submit proof")
        task.proof_note = payload.proofNote
        task.proof_image_urls = json.dumps(payload.proofImageUrls or [])
        _set_status(db, task, TaskStatus.PENDING_REVIEW, helper_id, "Proof submitted")
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def confirm_task(db: Session, task_id: str, requester_id: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.PENDING_REVIEW:
            raise TaskError("TASK_NOT_PENDING_REVIEW", "Task is not pending review")
        if task.requester_id != requester_id:
            raise TaskError("ONLY_REQUESTER_CAN_CONFIRM", "Only requester can confirm task")
        if task.helper_id is None:
            raise TaskError("TASK_HAS_NO_HELPER", "Task has no helper")
        settle_reward(db, task.requester_id, task.helper_id, task.reward, related_task_id=task.id)
        task.completed_at = _now()
        _set_status(db, task, TaskStatus.COMPLETED, requester_id, "Task confirmed")
        _recalculate_participant_credit(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def cancel_task(db: Session, task_id: str, requester_id: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.PENDING:
            raise TaskError("ONLY_PENDING_TASK_CAN_BE_CANCELLED", "Only pending tasks can be cancelled")
        if task.requester_id != requester_id:
            raise TaskError("ONLY_REQUESTER_CAN_CANCEL", "Only requester can cancel task")
        _set_status(db, task, TaskStatus.CANCELLED, requester_id, "Task cancelled")
        unfreeze_funds(db, task.requester_id, task.reward, related_task_id=task.id, description="Task cancelled refund")
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def abandon_task(db: Session, task_id: str, helper_id: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.IN_PROGRESS:
            raise TaskError("ONLY_IN_PROGRESS_TASK_CAN_BE_ABANDONED", "Only in-progress tasks can be abandoned")
        if task.helper_id != helper_id:
            raise TaskError("ONLY_ASSIGNED_HELPER_CAN_ABANDON", "Only assigned helper can abandon task")
        old_helper_id = task.helper_id
        task.helper_id = None
        _set_status(db, task, TaskStatus.PENDING, helper_id, "Helper abandoned task")
        db.flush()
        from app.services.credit_service import recalculate_user_credit

        recalculate_user_credit(db, old_helper_id, commit=False)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def reject_task(db: Session, task_id: str, requester_id: str, reason: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.PENDING_REVIEW:
            raise TaskError("ONLY_PENDING_REVIEW_TASK_CAN_BE_REJECTED", "Only pending-review tasks can be rejected")
        if task.requester_id != requester_id:
            raise TaskError("ONLY_REQUESTER_CAN_REJECT", "Only requester can reject task")
        _set_status(db, task, TaskStatus.DISPUTED, requester_id, reason)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def dispute_in_progress_task(db: Session, task_id: str, requester_id: str, reason: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.IN_PROGRESS:
            raise TaskError("ONLY_IN_PROGRESS_TASK_CAN_BE_DISPUTED", "Only in-progress tasks can be disputed")
        if task.requester_id != requester_id:
            raise TaskError("ONLY_REQUESTER_CAN_DISPUTE", "Only requester can dispute task")
        _set_status(db, task, TaskStatus.DISPUTED, requester_id, reason)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def resolve_dispute_for_helper(db: Session, task_id: str, admin_id: str, note: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.DISPUTED:
            raise TaskError("ONLY_DISPUTED_TASK_CAN_BE_RESOLVED", "Only disputed tasks can be resolved")
        if task.helper_id is None:
            raise TaskError("TASK_HAS_NO_HELPER", "Task has no helper")
        settle_reward(db, task.requester_id, task.helper_id, task.reward, related_task_id=task.id)
        task.completed_at = _now()
        _set_status(db, task, TaskStatus.COMPLETED, admin_id, note)
        _recalculate_participant_credit(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def resolve_dispute_for_requester(db: Session, task_id: str, admin_id: str, note: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.DISPUTED:
            raise TaskError("ONLY_DISPUTED_TASK_CAN_BE_RESOLVED", "Only disputed tasks can be resolved")
        unfreeze_funds(db, task.requester_id, task.reward, related_task_id=task.id, description="Dispute full refund")
        _set_status(db, task, TaskStatus.CANCELLED, admin_id, note)
        _recalculate_participant_credit(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def close_dispute_by_admin(db: Session, task_id: str, admin_id: str, note: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.DISPUTED:
            raise TaskError("ONLY_DISPUTED_TASK_CAN_BE_RESOLVED", "Only disputed tasks can be resolved")
        unfreeze_funds(db, task.requester_id, task.reward, related_task_id=task.id, description="Dispute closed by admin refund")
        _set_status(db, task, TaskStatus.CLOSED_BY_ADMIN, admin_id, note)
        _recalculate_participant_credit(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise


def resolve_dispute_split(db: Session, task_id: str, admin_id: str, helper_ratio: str | Decimal, note: str) -> Task:
    try:
        task = _load_task(db, task_id, for_update=True)
        if task.status != TaskStatus.DISPUTED:
            raise TaskError("ONLY_DISPUTED_TASK_CAN_BE_RESOLVED", "Only disputed tasks can be resolved")
        if task.helper_id is None:
            raise TaskError("TASK_HAS_NO_HELPER", "Task has no helper")
        settle_split(
            db,
            task.requester_id,
            task.helper_id,
            task.reward,
            helper_ratio=helper_ratio,
            related_task_id=task.id,
        )
        _set_status(db, task, TaskStatus.CLOSED_BY_ADMIN, admin_id, note)
        _recalculate_participant_credit(db, task)
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        raise
