"""
Recommendation rules for B-owned core business.

The frozen docs define four explainable signals and the output field contract.
This module keeps the first version deliberately simple: weighted rules only,
with optional weights read from system_configs when present.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.config import SystemConfig
from app.models.enums import TaskStatus
from app.models.map import CampusBuilding
from app.models.recommendation import RecommendationSnapshot
from app.models.task import Task, TaskLog
from app.models.user import User, UserProfile
from app.services.task_service import task_to_dict
from app.services.wallet_service import new_id
from app.utils.redis import get_redis_client

SCORE_QUANT = Decimal("0.01")
MAX_SCORE = Decimal("100.00")
DEFAULT_WEIGHTS = {
    "category": Decimal("25.00"),
    "distance": Decimal("25.00"),
    "successRate": Decimal("25.00"),
    "activeTime": Decimal("25.00"),
}
RECOMMENDATION_CACHE_TTL_SECONDS = 60


class RecommendationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _score(value: Decimal | int | str) -> Decimal:
    parsed = Decimal(str(value)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)
    return max(Decimal("0.00"), min(MAX_SCORE, parsed))


def _load_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise RecommendationError("USER_NOT_FOUND", "User not found")
    return user


def _json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _weights(db: Session) -> dict[str, Decimal]:
    config = db.get(SystemConfig, "recommendation.weights")
    if config is None:
        return DEFAULT_WEIGHTS.copy()
    raw = _json(config.config_value, {})
    weights = DEFAULT_WEIGHTS.copy()
    for key in weights:
        try:
            if key in raw:
                value = Decimal(str(raw[key]))
                if value >= 0:
                    weights[key] = value
        except (InvalidOperation, ValueError):
            weights[key] = DEFAULT_WEIGHTS[key]
    return weights


def _cache_key(user_id: str) -> str:
    return f"recommend:user:{user_id}"


def _cache_get(user_id: str, limit: int) -> list[dict] | None:
    try:
        cached = get_redis_client().get(_cache_key(user_id))
    except RedisError:
        return None
    if not cached:
        return None
    try:
        rows = json.loads(cached)
    except json.JSONDecodeError:
        return None
    return rows[:limit] if isinstance(rows, list) else None


def _cache_set(user_id: str, rows: list[dict]) -> None:
    try:
        get_redis_client().setex(
            _cache_key(user_id),
            RECOMMENDATION_CACHE_TTL_SECONDS,
            json.dumps(rows, ensure_ascii=False),
        )
    except RedisError:
        return None


def _profile(db: Session, user_id: str) -> UserProfile | None:
    return db.get(UserProfile, user_id)


def _category_score(task: Task, profile: UserProfile | None, weight: Decimal) -> Decimal:
    categories = _json(profile.preferred_categories if profile else None, [])
    if not categories:
        return _score(weight / Decimal("2"))
    return _score(weight if task.category.value in categories else Decimal("0.00"))


def _building(db: Session, code: str | None) -> CampusBuilding | None:
    if not code:
        return None
    return db.get(CampusBuilding, code)


def _distance_score(db: Session, task: Task, profile: UserProfile | None, weight: Decimal) -> Decimal:
    default_code = profile.default_building_code if profile else None
    if not default_code:
        return _score(weight / Decimal("2"))
    if default_code == task.building_code:
        return _score(weight)
    origin = _building(db, default_code)
    target = _building(db, task.building_code)
    if origin is None or target is None:
        return _score(weight / Decimal("2"))
    distance = math.dist(
        (float(origin.latitude), float(origin.longitude)),
        (float(target.latitude), float(target.longitude)),
    )
    distance_factor = max(0.0, 1.0 - min(distance, 1000.0) / 1000.0)
    return _score(weight * Decimal(str(distance_factor)))


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


def _computed_success_rate(db: Session, user_id: str) -> Decimal:
    completed = db.query(Task).filter(Task.helper_id == user_id, Task.status == TaskStatus.COMPLETED).count()
    abandoned = (
        db.query(TaskLog)
        .filter(
            TaskLog.actor_id == user_id,
            TaskLog.from_status == TaskStatus.IN_PROGRESS,
            TaskLog.to_status == TaskStatus.PENDING,
        )
        .count()
    )
    cancelled_tasks = db.query(Task).filter(Task.helper_id == user_id, Task.status == TaskStatus.CANCELLED).all()
    dispute_lost = sum(
        1
        for task in cancelled_tasks
        if _has_transition(db, task.id, TaskStatus.DISPUTED, TaskStatus.CANCELLED)
    )
    total = completed + abandoned + dispute_lost
    if total == 0:
        return Decimal("100.00")
    return _score(Decimal(completed) * Decimal("100.00") / Decimal(total))


def _success_rate_score(db: Session, user_id: str, profile: UserProfile | None, weight: Decimal) -> Decimal:
    if profile and profile.helper_success_rate is not None:
        success_rate = _score(profile.helper_success_rate)
    else:
        success_rate = _computed_success_rate(db, user_id)
    return _score(weight * success_rate / Decimal("100.00"))


def _active_time_score(task: Task, profile: UserProfile | None, weight: Decimal) -> Decimal:
    slots = _json(profile.active_time_slots if profile else None, [])
    if not slots:
        return _score(weight / Decimal("2"))
    task_hour = int((task.deadline or datetime.utcnow()).hour)
    if isinstance(slots, dict):
        slot_value = slots.get(str(task_hour), slots.get(task_hour))
        if slot_value is None:
            return Decimal("0.00")
        return _score(weight * _score(slot_value) / Decimal("100.00"))
    return _score(weight if task_hour in [int(hour) for hour in slots] else Decimal("0.00"))


def _snapshot(db: Session, user_id: str, task: Task, scores: dict[str, Decimal]) -> None:
    db.add(
        RecommendationSnapshot(
            id=new_id("rec"),
            user_id=user_id,
            task_id=task.id,
            score_total=scores["scoreTotal"],
            score_category=scores["scoreCategory"],
            score_distance=scores["scoreDistance"],
            score_success_rate=scores["scoreSuccessRate"],
            score_active_time=scores["scoreActiveTime"],
        )
    )


def _recommendation_reason(scores: dict[str, Decimal]) -> str:
    signals = [
        ("类别偏好", scores["scoreCategory"]),
        ("距离", scores["scoreDistance"]),
        ("履约成功率", scores["scoreSuccessRate"]),
        ("活跃时间", scores["scoreActiveTime"]),
    ]
    top = sorted(signals, key=lambda item: item[1], reverse=True)[:2]
    return "、".join(label for label, score in top if score > 0) or "基础推荐规则"


def _recommendation_payload(scores: dict[str, Decimal]) -> dict:
    return {
        "scoreTotal": float(scores["scoreTotal"]),
        "reason": _recommendation_reason(scores),
        "signals": {
            "category": float(scores["scoreCategory"]),
            "distance": float(scores["scoreDistance"]),
            "successRate": float(scores["scoreSuccessRate"]),
            "activeTime": float(scores["scoreActiveTime"]),
        },
    }


def _score_task(db: Session, user_id: str, task: Task, profile: UserProfile | None, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    scores = {
        "scoreCategory": _category_score(task, profile, weights["category"]),
        "scoreDistance": _distance_score(db, task, profile, weights["distance"]),
        "scoreSuccessRate": _success_rate_score(db, user_id, profile, weights["successRate"]),
        "scoreActiveTime": _active_time_score(task, profile, weights["activeTime"]),
    }
    scores["scoreTotal"] = _score(sum(scores.values(), Decimal("0.00")))
    return scores


def _item(db: Session, task: Task, scores: dict[str, Decimal]) -> dict:
    return {
        "task": task_to_dict(db, task),
        "scoreTotal": float(scores["scoreTotal"]),
        "scoreCategory": float(scores["scoreCategory"]),
        "scoreDistance": float(scores["scoreDistance"]),
        "scoreSuccessRate": float(scores["scoreSuccessRate"]),
        "scoreActiveTime": float(scores["scoreActiveTime"]),
        "recommendation": _recommendation_payload(scores),
    }


def build_recommendation_item(db: Session, user_id: str, task: Task) -> dict:
    _load_user(db, user_id)
    profile = _profile(db, user_id)
    weights = _weights(db)
    return _item(db, task, _score_task(db, user_id, task, profile, weights))


def list_recommended_tasks(db: Session, user_id: str, *, limit: int = 20) -> list[dict]:
    _load_user(db, user_id)
    cached = _cache_get(user_id, limit)
    if cached is not None:
        return cached
    profile = _profile(db, user_id)
    weights = _weights(db)
    tasks = (
        db.query(Task)
        .filter(Task.status == TaskStatus.PENDING, Task.requester_id != user_id)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .all()
    )
    ranked: list[tuple[Task, dict[str, Decimal]]] = []
    for task in tasks:
        scores = _score_task(db, user_id, task, profile, weights)
        ranked.append((task, scores))
    ranked.sort(key=lambda row: (row[1]["scoreTotal"], row[0].created_at or datetime.min, row[0].id), reverse=True)
    selected = ranked[:limit]
    for task, scores in selected:
        _snapshot(db, user_id, task, scores)
    db.commit()
    rows = [_item(db, task, scores) for task, scores in selected]
    _cache_set(user_id, rows)
    return rows
