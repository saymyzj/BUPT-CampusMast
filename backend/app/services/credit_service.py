from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.config import SystemConfig
from app.models.enums import TaskStatus
from app.models.rating import CreditSnapshot, Rating
from app.models.task import Task, TaskLog
from app.models.user import User
from app.services.wallet_service import new_id

SCORE_QUANT = Decimal("0.01")
ZERO = Decimal("0.00")
FULL_SCORE = Decimal("100.00")

HELPER_WEIGHTS = {
    "completion_rate": Decimal("0.35"),
    "average_rating": Decimal("0.25"),
    "timeout_rate": Decimal("0.15"),
    "abandon_rate": Decimal("0.15"),
    "dispute_lose_rate": Decimal("0.10"),
}

REQUESTER_WEIGHTS = {
    "completion_rate": Decimal("0.35"),
    "average_rating": Decimal("0.25"),
    "timeout_rate": Decimal("0.15"),
    "malicious_dispute_rate": Decimal("0.15"),
    "post_accept_cancel_rate": Decimal("0.10"),
}
OVERALL_WEIGHTS = {
    "helper": Decimal("0.60"),
    "requester": Decimal("0.40"),
}


class CreditError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _load_task(db: Session, task_id: str) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise CreditError("TASK_NOT_FOUND", "Task not found")
    return task


def _load_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise CreditError("USER_NOT_FOUND", "User not found")
    return user


def _score(value: Decimal | int | str) -> Decimal:
    return max(ZERO, min(FULL_SCORE, Decimal(str(value)))).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)


def _json(value: str | None) -> dict:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _configured_weights(db: Session) -> tuple[dict[str, Decimal], dict[str, Decimal], dict[str, Decimal]]:
    config = db.get(SystemConfig, "credit.weights")
    raw = _json(config.config_value if config else None)
    helper_weights = HELPER_WEIGHTS.copy()
    requester_weights = REQUESTER_WEIGHTS.copy()
    overall_weights = OVERALL_WEIGHTS.copy()
    for target, defaults in (
        (raw.get("helper", {}), helper_weights),
        (raw.get("requester", {}), requester_weights),
        (raw.get("overall", {}), overall_weights),
    ):
        if not isinstance(target, dict):
            continue
        for key in defaults:
            try:
                if key in target:
                    value = Decimal(str(target[key]))
                    if value >= 0:
                        defaults[key] = value
            except (InvalidOperation, ValueError):
                continue
    return helper_weights, requester_weights, overall_weights


def _rate(part: int, total: int) -> Decimal:
    if total <= 0:
        return FULL_SCORE
    return _score(Decimal(part) * FULL_SCORE / Decimal(total))


def _average_rating_score(db: Session, user_id: str) -> Decimal:
    ratings = db.execute(select(Rating.score).where(Rating.to_user_id == user_id)).scalars().all()
    if not ratings:
        return FULL_SCORE
    average = Decimal(sum(ratings)) / Decimal(len(ratings))
    return _score(average * Decimal("20"))


def _has_transition(db: Session, task_id: str, from_status: TaskStatus, to_status: TaskStatus) -> bool:
    return (
        db.execute(
            select(TaskLog.id).where(
                TaskLog.task_id == task_id,
                TaskLog.from_status == from_status,
                TaskLog.to_status == to_status,
            )
        ).first()
        is not None
    )


def _transition_time(db: Session, task_id: str, from_status: TaskStatus, to_status: TaskStatus):
    return (
        db.execute(
            select(TaskLog.created_at)
            .where(
                TaskLog.task_id == task_id,
                TaskLog.from_status == from_status,
                TaskLog.to_status == to_status,
            )
            .order_by(TaskLog.created_at.asc(), TaskLog.id.asc())
        )
        .scalars()
        .first()
    )


def _transition_actor(db: Session, task_id: str, from_status: TaskStatus, to_status: TaskStatus) -> str | None:
    return (
        db.execute(
            select(TaskLog.actor_id)
            .where(
                TaskLog.task_id == task_id,
                TaskLog.from_status == from_status,
                TaskLog.to_status == to_status,
            )
            .order_by(TaskLog.created_at.asc(), TaskLog.id.asc())
        )
        .scalars()
        .first()
    )


def _has_post_accept_cancel_trace(db: Session, task: Task, requester_id: str) -> bool:
    return (
        task.status == TaskStatus.CANCELLED
        and _has_transition(db, task.id, TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        and _transition_actor(db, task.id, TaskStatus.DISPUTED, TaskStatus.CANCELLED) == requester_id
    )


def _helper_timed_out(db: Session, task: Task) -> bool:
    proof_time = _transition_time(db, task.id, TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW)
    finished_at = proof_time or task.completed_at
    return bool(finished_at and task.deadline and finished_at > task.deadline)


def _requester_timed_out(db: Session, task: Task) -> bool:
    review_time = _transition_time(db, task.id, TaskStatus.PENDING_REVIEW, TaskStatus.COMPLETED)
    if review_time is None:
        review_time = _transition_time(db, task.id, TaskStatus.PENDING_REVIEW, TaskStatus.DISPUTED)
    return bool(review_time and task.deadline and review_time > task.deadline)


def _transition_count(db: Session, user_id: str, from_status: TaskStatus, to_status: TaskStatus) -> int:
    return (
        db.query(TaskLog)
        .filter(
            TaskLog.actor_id == user_id,
            TaskLog.from_status == from_status,
            TaskLog.to_status == to_status,
        )
        .count()
    )


def _helper_metrics(db: Session, user_id: str) -> dict[str, Decimal]:
    completed_tasks = db.query(Task).filter(Task.helper_id == user_id, Task.status == TaskStatus.COMPLETED).all()
    completed = len(completed_tasks)
    abandoned = _transition_count(db, user_id, TaskStatus.IN_PROGRESS, TaskStatus.PENDING)
    disputed_tasks = db.query(Task).filter(Task.helper_id == user_id, Task.status == TaskStatus.CANCELLED).all()
    dispute_lost = sum(
        1
        for task in disputed_tasks
        if _has_transition(db, task.id, TaskStatus.DISPUTED, TaskStatus.CANCELLED)
    )
    timed_out = sum(1 for task in completed_tasks if _helper_timed_out(db, task))
    total = completed + abandoned + dispute_lost
    if total == 0:
        return {
            "completion_rate": FULL_SCORE,
            "average_rating": FULL_SCORE,
            "timeout_rate": ZERO,
            "abandon_rate": ZERO,
            "dispute_lose_rate": ZERO,
        }
    return {
        "completion_rate": _rate(completed, total),
        "average_rating": _average_rating_score(db, user_id),
        "timeout_rate": _rate(timed_out, total),
        "abandon_rate": _rate(abandoned, total),
        "dispute_lose_rate": _rate(dispute_lost, total),
    }


def _requester_metrics(db: Session, user_id: str) -> dict[str, Decimal]:
    terminal_statuses = (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.EXPIRED, TaskStatus.CLOSED_BY_ADMIN)
    tasks = db.query(Task).filter(Task.requester_id == user_id, Task.status.in_(terminal_statuses)).all()
    if not tasks:
        return {
            "completion_rate": FULL_SCORE,
            "average_rating": FULL_SCORE,
            "timeout_rate": ZERO,
            "malicious_dispute_rate": ZERO,
            "post_accept_cancel_rate": ZERO,
        }
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    timed_out = sum(1 for task in tasks if _requester_timed_out(db, task))
    malicious_disputes = sum(
        1
        for task in tasks
        if task.status == TaskStatus.COMPLETED
        and _has_transition(db, task.id, TaskStatus.DISPUTED, TaskStatus.COMPLETED)
    )
    post_accept_cancels = sum(1 for task in tasks if _has_post_accept_cancel_trace(db, task, user_id))
    return {
        "completion_rate": _rate(completed, len(tasks)),
        "average_rating": _average_rating_score(db, user_id),
        "timeout_rate": _rate(timed_out, len(tasks)),
        "malicious_dispute_rate": _rate(malicious_disputes, len(tasks)),
        "post_accept_cancel_rate": _rate(post_accept_cancels, len(tasks)),
    }


def _helper_score(metrics: dict[str, Decimal], weights: dict[str, Decimal]) -> Decimal:
    return _score(
        metrics["completion_rate"] * weights["completion_rate"]
        + metrics["average_rating"] * weights["average_rating"]
        + (FULL_SCORE - metrics["timeout_rate"]) * weights["timeout_rate"]
        + (FULL_SCORE - metrics["abandon_rate"]) * weights["abandon_rate"]
        + (FULL_SCORE - metrics["dispute_lose_rate"]) * weights["dispute_lose_rate"]
    )


def _requester_score(metrics: dict[str, Decimal], weights: dict[str, Decimal]) -> Decimal:
    return _score(
        metrics["completion_rate"] * weights["completion_rate"]
        + metrics["average_rating"] * weights["average_rating"]
        + (FULL_SCORE - metrics["timeout_rate"]) * weights["timeout_rate"]
        + (FULL_SCORE - metrics["malicious_dispute_rate"]) * weights["malicious_dispute_rate"]
        + (FULL_SCORE - metrics["post_accept_cancel_rate"]) * weights["post_accept_cancel_rate"]
    )


def _snapshot(db: Session, user_id: str, role_scope: str, metrics: dict[str, Decimal], score: Decimal) -> CreditSnapshot:
    snapshot = CreditSnapshot(
        id=new_id("credit"),
        user_id=user_id,
        role_scope=role_scope,
        completion_rate=metrics["completion_rate"],
        average_rating=metrics["average_rating"],
        timeout_rate=metrics["timeout_rate"],
        abandon_rate=metrics.get("abandon_rate"),
        dispute_lose_rate=metrics.get("dispute_lose_rate"),
        malicious_dispute_rate=metrics.get("malicious_dispute_rate"),
        post_accept_cancel_rate=metrics.get("post_accept_cancel_rate"),
        calculated_score=score,
    )
    db.add(snapshot)
    return snapshot


def _rating_partner(task: Task, from_user_id: str) -> str:
    if task.status != TaskStatus.COMPLETED:
        raise CreditError("TASK_NOT_COMPLETED", "Only completed tasks can be rated")
    if task.helper_id is None:
        raise CreditError("TASK_HAS_NO_HELPER", "Task has no helper")
    if from_user_id == task.requester_id:
        return task.helper_id
    if from_user_id == task.helper_id:
        return task.requester_id
    raise CreditError("RATING_USER_NOT_TASK_PARTICIPANT", "Only task participants can rate each other")


def _ensure_not_rated(db: Session, task_id: str, from_user_id: str) -> None:
    exists = db.execute(
        select(Rating).where(Rating.task_id == task_id, Rating.from_user_id == from_user_id)
    ).scalar_one_or_none()
    if exists is not None:
        raise CreditError("DUPLICATE_RATING", "User has already rated this task")


def _is_duplicate_rating_integrity_error(exc: IntegrityError) -> bool:
    message = str(exc.orig).lower()
    return (
        "uq_ratings_task_id_from_user_id" in message
        or "ratings.task_id" in message
        or ("duplicate" in message and "task_id" in message and "from_user_id" in message)
    )


def _touch_credit_snapshot_after_rating(_db: Session, _rating: Rating) -> None:
    recalculate_user_credit(_db, _rating.to_user_id, commit=False)


def rating_to_dict(rating: Rating) -> dict:
    return {
        "id": rating.id,
        "taskId": rating.task_id,
        "fromUserId": rating.from_user_id,
        "toUserId": rating.to_user_id,
        "score": rating.score,
        "comment": rating.comment,
        "createdAt": rating.created_at.isoformat() if rating.created_at else "",
    }


def rate_task_partner(db: Session, task_id: str, from_user_id: str, payload) -> Rating:
    if payload.score < 1 or payload.score > 5:
        raise CreditError("INVALID_RATING_SCORE", "Rating score must be between 1 and 5")
    try:
        task = _load_task(db, task_id)
        to_user_id = _rating_partner(task, from_user_id)
        _ensure_not_rated(db, task_id, from_user_id)
        rating = Rating(
            id=new_id("rating"),
            task_id=task_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            score=payload.score,
            comment=payload.comment,
        )
        db.add(rating)
        db.flush()
        _touch_credit_snapshot_after_rating(db, rating)
        db.commit()
        db.refresh(rating)
        return rating
    except IntegrityError as exc:
        db.rollback()
        if _is_duplicate_rating_integrity_error(exc):
            raise CreditError("DUPLICATE_RATING", "User has already rated this task") from exc
        raise
    except Exception:
        db.rollback()
        raise


def list_received_ratings(db: Session, user_id: str) -> list[Rating]:
    _load_user(db, user_id)
    return (
        db.execute(select(Rating).where(Rating.to_user_id == user_id).order_by(Rating.created_at.desc()))
        .scalars()
        .all()
    )


def credit_profile_to_dict(user: User) -> dict:
    return {
        "requesterCreditScore": float(_score(user.requester_credit_score)),
        "helperCreditScore": float(_score(user.helper_credit_score)),
        "overallCreditScore": float(_score(user.overall_credit_score)),
    }


def get_credit_profile(db: Session, user_id: str) -> dict:
    return credit_profile_to_dict(_load_user(db, user_id))


def get_credit_profile_with_stats(db: Session, user_id: str) -> dict:
    profile = get_credit_profile(db, user_id)
    ratings = list_received_ratings(db, user_id)
    profile["ratingCount"] = len(ratings)
    profile["averageRating"] = round(float(sum(rating.score for rating in ratings) / len(ratings)), 2) if ratings else 0.0
    return profile


def recalculate_user_credit(db: Session, user_id: str, *, commit: bool = True) -> dict:
    try:
        user = _load_user(db, user_id)
        helper_weights, requester_weights, overall_weights = _configured_weights(db)
        helper_metrics = _helper_metrics(db, user_id)
        requester_metrics = _requester_metrics(db, user_id)
        helper_score = _helper_score(helper_metrics, helper_weights)
        requester_score = _requester_score(requester_metrics, requester_weights)
        overall_score = _score(
            helper_score * overall_weights["helper"] + requester_score * overall_weights["requester"]
        )

        user.helper_credit_score = helper_score
        user.requester_credit_score = requester_score
        user.overall_credit_score = overall_score
        _snapshot(db, user_id, "helper", helper_metrics, helper_score)
        _snapshot(db, user_id, "requester", requester_metrics, requester_score)

        if commit:
            db.commit()
            db.refresh(user)
        return credit_profile_to_dict(user)
    except Exception:
        if commit:
            db.rollback()
        raise
